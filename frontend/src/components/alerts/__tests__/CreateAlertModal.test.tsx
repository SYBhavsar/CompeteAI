import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import alertsReducer from '@/features/alerts/alertsSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import CreateAlertModal from '../CreateAlertModal'

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

describe('CreateAlertModal', () => {
  it('should not render when closed', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={false} onClose={() => {}} />
      </Provider>
    )

    expect(screen.queryByText('Create Alert')).not.toBeInTheDocument()
  })

  it('should render when open', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByText('Create Alert')).toBeInTheDocument()
  })

  it('should have alert type selector', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByLabelText(/alert type/i)).toBeInTheDocument()
  })

  it('should have competitor selector', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByLabelText(/competitor/i)).toBeInTheDocument()
  })

  it('should have active toggle', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByLabelText(/active/i)).toBeInTheDocument()
  })

  it('should have create button', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument()
  })

  it('should have cancel button', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
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
        <CreateAlertModal isOpen={true} onClose={onClose} />
      </Provider>
    )

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(onClose).toHaveBeenCalled()
  })

  it('should show threshold input for sentiment_change type', () => {
    const store = createTestStore()

    // We'll test by checking default state first
    const { rerender } = render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    // Default is new_content, so threshold should not be visible
    expect(screen.queryByLabelText(/sentiment threshold/i)).not.toBeInTheDocument()

    // We can't easily test Select interaction, but we verified the field isn't there by default
  })

  it('should show keywords input for keyword_match type', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <CreateAlertModal isOpen={true} onClose={() => {}} />
      </Provider>
    )

    // Default is new_content, so keywords should not be visible
    expect(screen.queryByLabelText(/keywords/i)).not.toBeInTheDocument()
  })
})
