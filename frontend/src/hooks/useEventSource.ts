import { useEffect } from "react";

/**
 * 범용 SSE 구독 hook. api/client.ts의 subscribeToEvents(), api/agentClient.ts의
 * subscribeToAgentEvents() 둘 다 동일한 EventSource + onmessage + JSON.parse
 * 메커니즘을 중복 구현하고 있던 것을 하나로 뽑았다 — url만 다르고 나머지 로직은
 * 완전히 동일했기 때문 (DRY).
 *
 * url이 null이면 구독하지 않는다 (아직 run_id/analysis_id가 없는 상태 등).
 */
export function useEventSource<TEvent>(
  url: string | null,
  onEvent: (event: TEvent) => void,
  onError?: (err: Event) => void,
): void {
  useEffect(() => {
    if (!url) return;
    const source = new EventSource(url);
    source.onmessage = (ev) => {
      try {
        onEvent(JSON.parse(ev.data) as TEvent);
      } catch {
        // JSON 파싱 실패는 무시 (keep-alive ping 등)
      }
    };
    source.onerror = (err) => {
      onError?.(err);
    };
    return () => source.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);
}
