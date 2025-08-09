package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
)

const ContractVersion = "v1"

type Event struct {
	Method  string              `json:"method"`
	Path    string              `json:"path"`
	Query   map[string][]string `json:"query"`
	Headers map[string]string   `json:"headers"`
	Body    []byte              `json:"body,omitempty"`
}

type Context struct {
	FunctionID      string `json:"function_id"`
	RequestID       string `json:"request_id"`
	ContractVersion string `json:"contract_version"`
}

type Result struct {
	StatusCode int               `json:"statusCode"`
	Headers    map[string]string `json:"headers,omitempty"`
	Body       any               `json:"body,omitempty"`
}

type HandlerFunc func(Event, Context) (Result, error)

var functionID = os.Getenv("FAAS_FUNCTION_ID")

func adapt(h HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		reqID := uuid.NewString()

		ev := Event{
			Method:  r.Method,
			Path:    r.URL.Path,
			Query:   r.URL.Query(),
			Headers: map[string]string{},
		}
		for k, v := range r.Header {
			if len(v) > 0 {
				ev.Headers[k] = v[0]
			}
		}
		if b, err := readBody(r); err == nil && len(b) > 0 {
			ev.Body = b
		}

		ctx := Context{
			FunctionID:      functionID,
			RequestID:       reqID,
			ContractVersion: ContractVersion,
		}

		res, err := h(ev, ctx)
		if err != nil {
			logJSON("error", map[string]any{
				"msg":         "request_error",
				"error":       err.Error(),
				"request_id":  reqID,
				"function_id": functionID,
				"duration_ms": time.Since(start).Milliseconds(),
			})
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "internal"})
			return
		}

		if res.Headers != nil {
			for k, v := range res.Headers {
				w.Header().Set(k, v)
			}
		}
		if res.StatusCode == 0 {
			res.StatusCode = 200
		}
		w.WriteHeader(res.StatusCode)
		if res.Body != nil {
			_ = json.NewEncoder(w).Encode(res.Body)
		}
		logJSON("info", map[string]any{
			"msg":         "request_ok",
			"status":      res.StatusCode,
			"request_id":  reqID,
			"function_id": functionID,
			"duration_ms": time.Since(start).Milliseconds(),
		})
	}
}

func logJSON(level string, payload map[string]any) {
	payload["level"] = level
	b, _ := json.Marshal(payload)
	log.Println(string(b))
}

func readBody(r *http.Request) ([]byte, error) {
	defer r.Body.Close()
	return io.ReadAll(r.Body)
}
