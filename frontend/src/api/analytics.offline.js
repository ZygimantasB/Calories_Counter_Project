// Offline analytics API: same exports/signatures, backed by local SQLite.
import { getAnalytics, monthCompare, yearlyTrends } from '../logic/analytics';

export const analyticsApi = {
  getAnalytics: (params = {}) => getAnalytics(params),
  getMonthCompare: (monthA, monthB) => monthCompare(monthA, monthB),
  getYearlyTrends: (year = 'last12') => yearlyTrends(year),
};

export default analyticsApi;
