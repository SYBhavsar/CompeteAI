import '@testing-library/jest-dom'

// Mock ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver

// Mock localStorage
const localStorageMock: Storage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
  clear: () => {},
  length: 0,
  key: () => null,
}
Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
})
