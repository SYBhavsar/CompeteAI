import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import api from '@/services/api'
import { SearchResult, SearchFilters, SavedSearch, SearchHistory } from '@/types'

interface SearchState {
  searchType: 'semantic' | 'traditional'
  query: string
  filters: SearchFilters
  results: SearchResult[]
  total: number
  loading: boolean
  error: string | null
  savedSearches: SavedSearch[]
  searchHistory: SearchHistory[]
}

const initialState: SearchState = {
  searchType: 'semantic',
  query: '',
  filters: {
    dateFrom: null,
    dateTo: null,
    competitorIds: [],
    sentiment: null,
  },
  results: [],
  total: 0,
  loading: false,
  error: null,
  savedSearches: [],
  searchHistory: [],
}

// Async thunks
export const performSearch = createAsyncThunk(
  'search/performSearch',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as { search: SearchState }
      const { searchType, query, filters } = state.search

      const endpoint = searchType === 'semantic' ? '/search/semantic' : '/search/traditional'
      const method = searchType === 'semantic' ? 'post' : 'get'

      const response =
        method === 'post'
          ? await api.post(endpoint, { query, filters })
          : await api.get(endpoint, { params: { query, ...filters } })

      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Search failed')
    }
  }
)

export const fetchSavedSearches = createAsyncThunk(
  'search/fetchSavedSearches',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/search/saved')
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch saved searches')
    }
  }
)

export const fetchSearchHistory = createAsyncThunk(
  'search/fetchSearchHistory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/search/history')
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch search history')
    }
  }
)

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setSearchType: (state, action: PayloadAction<'semantic' | 'traditional'>) => {
      state.searchType = action.payload
    },
    setQuery: (state, action: PayloadAction<string>) => {
      state.query = action.payload
    },
    setFilters: (state, action: PayloadAction<SearchFilters>) => {
      state.filters = action.payload
    },
    clearSearch: (state) => {
      state.query = ''
      state.results = []
      state.total = 0
      state.error = null
    },
    clearFilters: (state) => {
      state.filters = {
        dateFrom: null,
        dateTo: null,
        competitorIds: [],
        sentiment: null,
      }
    },
  },
  extraReducers: (builder) => {
    // Perform search
    builder.addCase(performSearch.pending, (state) => {
      state.loading = true
      state.error = null
    })
    builder.addCase(performSearch.fulfilled, (state, action) => {
      state.loading = false
      state.results = action.payload.results || []
      state.total = action.payload.total || 0
    })
    builder.addCase(performSearch.rejected, (state, action) => {
      state.loading = false
      state.error = action.payload as string
    })

    // Fetch saved searches
    builder.addCase(fetchSavedSearches.fulfilled, (state, action) => {
      state.savedSearches = action.payload
    })

    // Fetch search history
    builder.addCase(fetchSearchHistory.fulfilled, (state, action) => {
      state.searchHistory = action.payload
    })
  },
})

export const { setSearchType, setQuery, setFilters, clearSearch, clearFilters } =
  searchSlice.actions

export default searchSlice.reducer
