import { useEffect, useState } from 'react'

interface ResourceState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

export function useApiResource<T>(loader: (signal: AbortSignal) => Promise<T>): ResourceState<T> {
  const [state, setState] = useState<ResourceState<T>>({
    data: null,
    error: null,
    loading: true,
  })

  useEffect(() => {
    const controller = new AbortController()

    Promise.resolve()
      .then(() => {
        if (!controller.signal.aborted) {
          setState({ data: null, error: null, loading: true })
        }
        return loader(controller.signal)
      })
      .then((data) => {
        if (controller.signal.aborted) {
          return
        }
        setState({ data, error: null, loading: false })
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return
        }
        const message = error instanceof Error ? error.message : 'Request failed.'
        setState({ data: null, error: message, loading: false })
      })

    return () => controller.abort()
  }, [loader])

  return state
}
