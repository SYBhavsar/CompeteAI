import searchReducer, {
  setSearchType,
  setQuery,
  setFilters,
  clearSearch,
} from '../searchSlice'

describe('Search Slice', () => {
  const initialState = {
    searchType: 'semantic' as const,
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

  it('should return the initial state', () => {
    expect(searchReducer(undefined, { type: 'unknown' })).toEqual(initialState)
  })

  it('should handle setSearchType', () => {
    const actual = searchReducer(initialState, setSearchType('traditional'))
    expect(actual.searchType).toEqual('traditional')
  })

  it('should handle setQuery', () => {
    const actual = searchReducer(initialState, setQuery('test query'))
    expect(actual.query).toEqual('test query')
  })

  it('should handle setFilters', () => {
    const filters = {
      dateFrom: '2024-01-01',
      dateTo: '2024-12-31',
      competitorIds: [1, 2],
      sentiment: 'positive',
    }
    const actual = searchReducer(initialState, setFilters(filters))
    expect(actual.filters).toEqual(filters)
  })

  it('should handle clearSearch', () => {
    const stateWithData = {
      ...initialState,
      query: 'test',
      results: [{ id: 1, content: 'test' }],
      total: 1,
    }
    const actual = searchReducer(stateWithData, clearSearch())
    expect(actual.query).toEqual('')
    expect(actual.results).toEqual([])
    expect(actual.total).toEqual(0)
  })
})
