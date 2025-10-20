import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { Competitor } from '@/types'
import { competitorsService } from '@/services/competitorsService'

interface CompetitorsState {
  items: Competitor[]
  selectedCompetitor: Competitor | null
  loading: boolean
  error: string | null
}

const initialState: CompetitorsState = {
  items: [],
  selectedCompetitor: null,
  loading: false,
  error: null,
}

/**
 * Fetch all competitors from the API
 */
export const fetchCompetitorsAsync = createAsyncThunk(
  'competitors/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const competitors = await competitorsService.getAll()
      return competitors
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch competitors')
    }
  }
)

/**
 * Fetch a single competitor by ID
 */
export const fetchCompetitorByIdAsync = createAsyncThunk(
  'competitors/fetchById',
  async (id: number, { rejectWithValue }) => {
    try {
      const competitor = await competitorsService.getById(id)
      return competitor
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch competitor')
    }
  }
)

/**
 * Create a new competitor
 */
export const createCompetitorAsync = createAsyncThunk(
  'competitors/create',
  async (data: { name: string; domain?: string; industry?: string }, { rejectWithValue }) => {
    try {
      const competitor = await competitorsService.create(data)
      return competitor
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create competitor')
    }
  }
)

/**
 * Update an existing competitor
 */
export const updateCompetitorAsync = createAsyncThunk(
  'competitors/update',
  async (
    { id, data }: { id: number; data: { name?: string; domain?: string; industry?: string } },
    { rejectWithValue }
  ) => {
    try {
      const competitor = await competitorsService.update(id, data)
      return competitor
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update competitor')
    }
  }
)

/**
 * Delete a competitor
 */
export const deleteCompetitorAsync = createAsyncThunk(
  'competitors/delete',
  async (id: number, { rejectWithValue }) => {
    try {
      await competitorsService.delete(id)
      return id
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete competitor')
    }
  }
)

const competitorsSlice = createSlice({
  name: 'competitors',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    clearSelectedCompetitor: (state) => {
      state.selectedCompetitor = null
    },
  },
  extraReducers: (builder) => {
    // Fetch all competitors
    builder
      .addCase(fetchCompetitorsAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchCompetitorsAsync.fulfilled, (state, action: PayloadAction<Competitor[]>) => {
        state.loading = false
        state.items = action.payload
      })
      .addCase(fetchCompetitorsAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Fetch competitor by ID
    builder
      .addCase(fetchCompetitorByIdAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchCompetitorByIdAsync.fulfilled, (state, action: PayloadAction<Competitor>) => {
        state.loading = false
        state.selectedCompetitor = action.payload
      })
      .addCase(fetchCompetitorByIdAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Create competitor
    builder
      .addCase(createCompetitorAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(createCompetitorAsync.fulfilled, (state, action: PayloadAction<Competitor>) => {
        state.loading = false
        state.items.push(action.payload)
      })
      .addCase(createCompetitorAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Update competitor
    builder
      .addCase(updateCompetitorAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(updateCompetitorAsync.fulfilled, (state, action: PayloadAction<Competitor>) => {
        state.loading = false
        const index = state.items.findIndex((c) => c.id === action.payload.id)
        if (index !== -1) {
          state.items[index] = action.payload
        }
        if (state.selectedCompetitor?.id === action.payload.id) {
          state.selectedCompetitor = action.payload
        }
      })
      .addCase(updateCompetitorAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })

    // Delete competitor
    builder
      .addCase(deleteCompetitorAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(deleteCompetitorAsync.fulfilled, (state, action: PayloadAction<number>) => {
        state.loading = false
        state.items = state.items.filter((c) => c.id !== action.payload)
        if (state.selectedCompetitor?.id === action.payload) {
          state.selectedCompetitor = null
        }
      })
      .addCase(deleteCompetitorAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { clearError, clearSelectedCompetitor } = competitorsSlice.actions

// Selectors
export const selectCompetitors = (state: { competitors: CompetitorsState }) =>
  state.competitors.items
export const selectSelectedCompetitor = (state: { competitors: CompetitorsState }) =>
  state.competitors.selectedCompetitor
export const selectCompetitorsLoading = (state: { competitors: CompetitorsState }) =>
  state.competitors.loading
export const selectCompetitorsError = (state: { competitors: CompetitorsState }) =>
  state.competitors.error

export default competitorsSlice.reducer
