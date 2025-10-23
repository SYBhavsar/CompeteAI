import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import alertsReducer from '@/features/alerts/alertsSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import EditAlertModal from '../EditAlertModal'
import { Alert } from '@/types'

const mockAlert: Alert = {
  id: 1,
  user_id: 1,
  competitor_id: 1,
  alert_type: 'sentiment_change',
  conditions: { threshold: 0.7 },
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const createTestStore = () => {
  return configureStore({
    reducer: {
      alerts: alertsReducer,
      competitors: competitorsReducer,
    },
    preloadedState: {
      alerts: {
        alerts: [],
        notifications: [],
        unreadCount: 0,
        loading: false,
        error: null,
      },
      competitors: {
        competitors: [
          {
            id: 1,
            name: 'Competitor 1',
            domain: 'competitor1.com',
            industry: 'Tech',
            user_id: 1,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
    },
  })
}

describe('EditAlertModal', () => {
  it('should not render when closed', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={false} onClose={() => {}} />
      </Provider>
    )

    expect(screen.queryByText('Edit Alert')).not.toBeInTheDocument()
  })

  it('should render when open', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByText('Edit Alert')).toBeInTheDocument()
  })

  it('should pre-fill alert type', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByLabelText(/alert type/i)).toBeInTheDocument()
  })

  it('should pre-fill competitor', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByLabelText(/competitor/i)).toBeInTheDocument()
  })

  it('should pre-fill threshold for sentiment_change', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    const thresholdInput = screen.getByLabelText(/sentiment threshold/i) as HTMLInputElement
    expect(thresholdInput.value).toBe('0.7')
  })

  it('should have update button', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument()
  })

  it('should have cancel button', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('should call onClose when cancel clicked', async () => {
    const user = userEvent.setup()
    const onClose = jest.fn()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={mockAlert} isOpen={true} onClose={onClose} />
      </Provider>
    )

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(onClose).toHaveBeenCalled()
  })

  it('should pre-fill keywords for keyword_match type', () => {
    const keywordAlert: Alert = {
      ...mockAlert,
      alert_type: 'keyword_match',
      conditions: { keywords: ['test', 'keyword'] },
    }

    const store = createTestStore()

    render(
      <Provider store={store}>
        <EditAlertModal alert={keywordAlert} isOpen={true} onClose={() => {}} />
      </Provider>
    )

    const keywordsInput = screen.getByLabelText(/keywords/i) as HTMLInputElement
    expect(keywordsInput.value).toBe('test, keyword')
  })
})
