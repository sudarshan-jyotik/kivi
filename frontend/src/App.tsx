import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { SampleDemoBanner } from './components/SampleDemoBanner';
import { ReviewList } from './components/ReviewList';
import { ReviewDetail } from './components/ReviewDetail';
import { UploadModal } from './components/UploadModal';
import { api } from './services/api';
import { ReviewResponse, ReviewSummary } from './types';
import { AlertCircle, Server } from 'lucide-react';

export function App() {
  const [currentView, setCurrentView] = useState<'reviews' | 'detail'>('reviews');
  const [selectedReview, setSelectedReview] = useState<ReviewResponse | null>(null);
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isLoadingReviews, setIsLoadingReviews] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [activeDemo, setActiveDemo] = useState<number | null>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

  // Check backend server health
  const checkHealth = async () => {
    try {
      await api.checkHealth();
      setServerStatus('online');
    } catch {
      setServerStatus('offline');
    }
  };

  // Fetch reviews list
  const loadReviews = async () => {
    setIsLoadingReviews(true);
    try {
      const data = await api.listReviews();
      setReviews(data);
      setServerStatus('online');
    } catch (err) {
      console.error('Error loading reviews:', err);
      setServerStatus('offline');
    } finally {
      setIsLoadingReviews(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadReviews();
  }, []);

  // Fetch single review details
  const handleSelectReview = async (id: string) => {
    setIsLoadingDetail(true);
    try {
      const detail = await api.getReview(id);
      setSelectedReview(detail);
      setCurrentView('detail');
    } catch (err) {
      console.error('Error loading review details:', err);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Run sample demo 1, 2, or 3
  const handleRunDemo = async (sampleNumber: number) => {
    setActiveDemo(sampleNumber);
    setDemoError(null);
    try {
      const review = await api.runDemo(sampleNumber);
      setSelectedReview(review);
      setCurrentView('detail');
      loadReviews();
    } catch (err: any) {
      setDemoError(err.message || `Failed to run sample #${sampleNumber}.`);
    } finally {
      setActiveDemo(null);
    }
  };

  // Handle successful upload
  const handleUploadSuccess = (review: ReviewResponse) => {
    setIsUploadOpen(false);
    setSelectedReview(review);
    setCurrentView('detail');
    loadReviews();
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navigation */}
      <Navbar
        currentView={currentView}
        setCurrentView={(view) => {
          if (view === 'upload') {
            setIsUploadOpen(true);
          } else {
            setCurrentView(view);
          }
        }}
        serverStatus={serverStatus}
        onNewAuditClick={() => setIsUploadOpen(true)}
      />

      {/* Render Sleep Notification / Server Waking up banner */}
      {serverStatus === 'offline' && (
        <div className="bg-amber-500 text-white text-xs px-4 py-2 text-center flex items-center justify-center space-x-2 font-medium shadow-sm">
          <Server className="w-3.5 h-3.5 animate-pulse" />
          <span>
            Connecting to backend... If the service was inactive, it may take 30-50 seconds to wake up on Render's free tier.
          </span>
          <button
            onClick={() => {
              setServerStatus('checking');
              loadReviews();
            }}
            className="underline ml-2 hover:opacity-80"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Demo Error Banner */}
        {demoError && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{demoError}</span>
            </div>
            <button onClick={() => setDemoError(null)} className="text-rose-500 hover:text-rose-700">
              Dismiss
            </button>
          </div>
        )}

        {currentView === 'reviews' ? (
          <div>
            {/* Quick Demo Banner */}
            <SampleDemoBanner
              onRunDemo={handleRunDemo}
              isLoading={activeDemo !== null}
              activeDemoNumber={activeDemo}
            />

            {/* Past Audits List */}
            <ReviewList
              reviews={reviews}
              onSelectReview={handleSelectReview}
              isLoading={isLoadingReviews}
              onRefresh={loadReviews}
            />
          </div>
        ) : selectedReview ? (
          <ReviewDetail
            review={selectedReview}
            onBack={() => {
              setCurrentView('reviews');
              loadReviews();
            }}
            onDecisionUpdated={(updated) => {
              setSelectedReview(updated);
              loadReviews();
            }}
          />
        ) : (
          <div className="text-center py-20 text-slate-400 text-xs">
            {isLoadingDetail ? 'Loading review details...' : 'Review not found.'}
          </div>
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={handleUploadSuccess}
      />
    </div>
  );
}

export default App;
