import React, { Component } from 'react';
import { AlertTriangle, RotateCcw, Home, Clipboard } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    
    // Centralized detailed error logging
    console.group('%c[React Error Boundary] Uncaught Rendering Error', 'color: #ef4444; font-weight: bold; font-size: 14px;');
    console.error('Error Message:', error.message);
    console.error('Error Object:', error);
    console.error('Component Stack:', errorInfo.componentStack);
    console.log('Context Info:', {
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    });
    console.groupEnd();
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.hash = '#/';
    window.location.reload();
  };

  handleCopyError = () => {
    const errorLog = `
Error: ${this.state.error?.message || this.state.error}
Stack Trace: ${this.state.error?.stack}
Component Stack: ${this.state.errorInfo?.componentStack}
URL: ${window.location.href}
Time: ${new Date().toISOString()}
User Agent: ${navigator.userAgent}
    `.trim();
    
    navigator.clipboard.writeText(errorLog).then(() => {
      alert('Error details copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy error details:', err);
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-950 p-6 font-sans">
          <div className="max-w-xl w-full bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
            {/* Top decorative gradient accent */}
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-red-500 via-orange-500 to-red-600" />
            
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-red-950/50 border border-red-500/30 rounded-2xl flex items-center justify-center mb-6 text-red-400">
                <AlertTriangle className="w-8 h-8" />
              </div>
              
              <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
              <p className="text-gray-400 mb-6 text-sm max-w-sm">
                An unexpected UI rendering error occurred. The application state has been halted safely to prevent data loss.
              </p>

              {/* Error Details Console View */}
              <div className="w-full bg-gray-950/60 border border-gray-800/80 rounded-xl p-4 text-left mb-6 max-h-48 overflow-y-auto">
                <div className="text-red-400 font-mono text-xs font-semibold mb-1 break-all">
                  {this.state.error?.toString()}
                </div>
                {this.state.errorInfo && (
                  <pre className="text-gray-500 font-mono text-[10px] leading-relaxed select-text whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>

              {/* Action Triggers */}
              <div className="flex flex-wrap gap-3 justify-center w-full">
                <button
                  onClick={this.handleReload}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white font-medium rounded-xl shadow-lg shadow-primary-950/20 active:scale-[0.98] transition duration-150 text-sm cursor-pointer"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reload Page
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium rounded-xl border border-gray-700 active:scale-[0.98] transition duration-150 text-sm cursor-pointer"
                >
                  <Home className="w-4 h-4" />
                  Go to Dashboard
                </button>
                <button
                  onClick={this.handleCopyError}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium rounded-xl border border-gray-700 active:scale-[0.98] transition duration-150 text-sm cursor-pointer"
                >
                  <Clipboard className="w-4 h-4" />
                  Copy Details
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
