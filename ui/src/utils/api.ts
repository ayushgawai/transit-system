/**
 * API URL utility
 * Automatically detects if running locally or on CloudFront
 * and uses appropriate backend URL
 */
export const getApiBaseUrl = (): string => {
  // Check if we're running on CloudFront (production)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // If on CloudFront, use ALB backend
    if (hostname.includes('cloudfront.net')) {
      return 'http://transit-alb-dev-415359952.us-west-2.elb.amazonaws.com/api';
    }
    
    // If on localhost, use local backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000/api';
    }
  }
  
  // Fallback: use environment variable or default
  return (import.meta as any).env.VITE_API_URL || 'http://localhost:8000/api';
};

export const getBackendBaseUrl = (): string => {
  return getApiBaseUrl().replace('/api', '');
};

