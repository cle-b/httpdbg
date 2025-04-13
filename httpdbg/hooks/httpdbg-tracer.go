package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"net/http/httputil"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

var traceLogMutex sync.Mutex
var traceList []TraceEntry

type StackFrame struct {
	FuncName string `json:"func_name"`
	Location string `json:"location"`
	Code     string `json:"code"`
}

type Initiator struct {
	Filename string       `json:"filename"`
	Lineno   int          `json:"lineno"`
	FuncName string       `json:"func_name"`
	Code     string       `json:"code"`
	Stack    []StackFrame `json:"stack"`
}

type TraceEntry struct {
	TraceID      string    `json:"trace_id"`
	Timestamp    string    `json:"timestamp"`
	EndTimestamp string    `json:"end_timestamp"`
	Initiator    Initiator `json:"initiator"`
	RequestFile  string    `json:"request_file"`
	ResponseFile string    `json:"response_file"`
}

func init() {
	defaultTransport := http.DefaultTransport.(*http.Transport)

	http.DefaultTransport = &tracingTransport{
		inner: defaultTransport,
	}
}

func min(a, b int) int { //TODO to replace by cmp.Min
	if a < b {
		return a
	}
	return b
}
func max(a, b int) int { //TODO to replace by cmp.Max
	if a > b {
		return a
	}
	return b
}

func getHttpdbgDir() string {
	outputDir := os.Getenv("HTTPDBG_MULTIPROCESS_DIR")
	if outputDir == "" {
		log.Printf("httpdbg -HTTPDBG_MULTIPROCESS_DIR not set")
	}
	return outputDir
}

type tracingTransport struct {
	inner *http.Transport
}

func getInitiator() Initiator {
	pcs := make([]uintptr, 32)
	n := runtime.Callers(3, pcs)
	frames := runtime.CallersFrames(pcs[:n])

	var fullStack []StackFrame
	var selectedFrame *runtime.Frame

	for {
		frame, more := frames.Next()

		entry := StackFrame{
			FuncName: frame.Function,
			Location: fmt.Sprintf("%s:%d", filepath.Base(frame.File), frame.Line),
			Code:     readSourceLine(frame.File, frame.Line), // default single line
		}

		if selectedFrame == nil &&
			!strings.Contains(frame.Function, "net/http") &&
			!strings.Contains(frame.Function, "runtime.") {

			selectedFrame = &frame

			// Replace single line with full context as one string
			contextLines := readCodeContextLines(frame.File, frame.Line, 4)
			entry.Code = strings.Join(contextLines, "\n")

			fullStack = append(fullStack, entry)
			break // stop after the initiator
		} else {
			fullStack = append(fullStack, entry)
		}

		if !more {
			break
		}
	}

	if selectedFrame == nil {
		selectedFrame = &runtime.Frame{
			File:     "unknown",
			Line:     0,
			Function: "unknown",
		}
		fullStack = append(fullStack, StackFrame{
			FuncName: "unknown",
			Location: "unknown:0",
			Code:     "<source unavailable>",
		})
	}

	return Initiator{
		Filename: filepath.Base(selectedFrame.File),
		Lineno:   selectedFrame.Line,
		FuncName: selectedFrame.Function,
		Code:     readSourceLine(selectedFrame.File, selectedFrame.Line),
		Stack:    fullStack,
	}
}

func readCodeContextLines(filename string, centerLine, padding int) []string {
	data, err := os.ReadFile(filename)
	if err != nil {
		return []string{"<source unavailable>"}
	}
	lines := strings.Split(string(data), "\n")
	start := max(centerLine-padding-1, 0)
	end := min(centerLine+padding, len(lines))

	var context []string
	for i := start; i < end; i++ {
		line := lines[i]
		if i == centerLine-1 {
			context = append(context, line+" <====")
		} else {
			context = append(context, line)
		}
	}
	return context
}

func readSourceLine(filename string, line int) string {
	data, err := os.ReadFile(filename)
	if err != nil {
		return "source unavailable"
	}
	lines := strings.Split(string(data), "\n")
	if line >= 1 && line <= len(lines) {
		return strings.TrimSpace(lines[line-1])
	}
	return "line out of range"
}

func (t *tracingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	traceID := generateTraceID()
	startTime := time.Now().UTC()
	timestamp := startTime.Format(time.RFC3339Nano)
	outputDir := getHttpdbgDir()
	initiator := getInitiator()

	// Read request body (must buffer + re-inject)
	var reqBody []byte
	if req.Body != nil {
		reqBody, _ = io.ReadAll(req.Body)
		req.Body = io.NopCloser(bytes.NewReader(reqBody))
	}

	requestFile := filepath.Join(outputDir, fmt.Sprintf("%s-request.txt", traceID))
	dump, err := httputil.DumpRequestOut(req, true)
	if err != nil {
		log.Printf("httpdbg -Failed to dump request: %v", err)
	} else {
		err = os.WriteFile(requestFile, dump, 0644)
		if err != nil {
			log.Printf("httpdbg -Failed to write request file: %v", err)
		}
	}

	resp, err := t.inner.RoundTrip(req)
	if err != nil { // TODO trace failure
		return nil, err
	}

	// Read response body (must buffer + re-inject)
	var respBody []byte
	if resp.Body != nil {
		respBody, _ = io.ReadAll(resp.Body)
		resp.Body = io.NopCloser(bytes.NewReader(respBody))
	}

	responseFile := filepath.Join(outputDir, fmt.Sprintf("%s-response.txt", traceID))
	dumpResp, err := httputil.DumpResponse(resp, true)
	if err != nil {
		log.Printf("httpdbg -Failed to dump response: %v", err)
	} else {
		err = os.WriteFile(responseFile, dumpResp, 0644)
		if err != nil {
			log.Printf("httpdbg -Failed to write response file: %v", err)
		}
	}

	endTime := time.Now().UTC()
	endTimestamp := endTime.Format(time.RFC3339Nano)

	// Write trace index entry
	entry := TraceEntry{
		TraceID:      traceID,
		Timestamp:    timestamp,
		EndTimestamp: endTimestamp,
		Initiator:    initiator,
		RequestFile:  requestFile,
		ResponseFile: responseFile,
	}

	appendToTraceIndex(entry)

	return resp, nil
}

func generateTraceID() string {
	return fmt.Sprintf("go-%d-%d", time.Now().UnixNano(), rand.Intn(10000))
}

func appendToTraceIndex(entry TraceEntry) {
	traceLogMutex.Lock()
	defer traceLogMutex.Unlock()

	traceList = append(traceList, entry)

	dir := getHttpdbgDir()
	tmpFile := filepath.Join(dir, "httpdbg-go-traces.json.tmp")
	finalFile := filepath.Join(dir, "httpdbg-go-traces.json")

	// Write to temp file
	f, err := os.Create(tmpFile)
	if err != nil {
		log.Printf("httpdbg -Failed to create temp trace file: %v", err)
		return
	}
	defer f.Close()

	encoder := json.NewEncoder(f)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(traceList); err != nil {
		log.Printf("httpdbg -Failed to encode trace list: %v", err)
		return
	}

	// Atomically rename to final file
	if err := os.Rename(tmpFile, finalFile); err != nil {
		log.Printf("httpdbg -Failed to rename temp trace file: %v", err)
	}
}
