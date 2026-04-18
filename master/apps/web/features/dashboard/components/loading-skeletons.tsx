type DocumentsPageSkeletonProps = {
	cardCount?: number;
	showComposer?: boolean;
};

function SkeletonBox({ className = '' }: { className?: string }) {
	return <span className={`ui-skeleton ${className}`.trim()} aria-hidden="true" />;
}

function AppTopbarSkeleton() {
	return (
		<header className="dash-topbar dash-topbar-skeleton" aria-hidden="true">
			<div className="dash-brand">
				<SkeletonBox className="dash-skeleton-dot" />
				<SkeletonBox className="dash-skeleton-brand" />
			</div>
			<div className="dash-nav dash-nav-skeleton">
				<SkeletonBox className="dash-skeleton-pill" />
				<SkeletonBox className="dash-skeleton-pill" />
				<SkeletonBox className="dash-skeleton-pill" />
				<SkeletonBox className="dash-skeleton-pill" />
			</div>
			<div className="dash-userbar">
				<SkeletonBox className="dash-skeleton-avatar" />
			</div>
		</header>
	);
}

export function DocumentsPageSkeleton({
	cardCount = 6,
	showComposer = false,
}: DocumentsPageSkeletonProps) {
	return (
		<main className="dashboard-shell documents-page documents-page-skeleton">
			<AppTopbarSkeleton />

			<section className="documents-toolbar documents-toolbar-skeleton" aria-hidden="true">
				<SkeletonBox className="documents-skeleton-search" />
				<SkeletonBox className="documents-skeleton-select" />
				<SkeletonBox className="documents-skeleton-select" />
				<SkeletonBox className="documents-skeleton-select" />
			</section>

			<SkeletonBox className="documents-skeleton-count" />

			<section className="documents-grid" aria-hidden="true">
				{Array.from({ length: cardCount }).map((_, index) => (
					<article key={index} className="documents-card documents-card-skeleton">
						<div className="documents-card-top">
							<SkeletonBox className="documents-skeleton-kicker" />
							<SkeletonBox className="documents-skeleton-title" />
							<SkeletonBox className="documents-skeleton-title documents-skeleton-title-short" />
							<SkeletonBox className="documents-skeleton-stat" />
							<SkeletonBox className="documents-skeleton-meta" />
						</div>
						<div className="documents-card-bottom">
							<div className="documents-tags">
								<SkeletonBox className="documents-skeleton-tag" />
							</div>
							<div className="documents-card-actions">
								<SkeletonBox className="documents-skeleton-button" />
							</div>
						</div>
					</article>
				))}
			</section>

			{showComposer ? (
				<div className="practice-composer-dock practice-composer-dock-skeleton" aria-hidden="true">
					<div className="practice-composer-shell">
						<SkeletonBox className="practice-skeleton-input" />
						<SkeletonBox className="practice-skeleton-send" />
					</div>
				</div>
			) : null}
		</main>
	);
}

export function DashboardPageSkeleton() {
	return (
		<main className="dashboard-shell dashboard-shell-skeleton">
			<AppTopbarSkeleton />

			<section className="dash-progress-layout" aria-hidden="true">
				<div className="dash-history-column">
					<section className="dash-panel dash-panel-skeleton">
						<div className="dash-panel-head dash-panel-head-skeleton">
							<SkeletonBox className="dash-skeleton-heading" />
							<SkeletonBox className="dash-skeleton-copy" />
						</div>

						<div className="dash-history-feed dash-history-feed-skeleton">
							{Array.from({ length: 3 }).map((_, index) => (
								<div key={index} className="dash-history-item dash-history-item-skeleton">
									<div className="dash-history-main">
										<div className="dash-history-topline">
											<SkeletonBox className="dash-skeleton-badge" />
											<SkeletonBox className="dash-skeleton-time" />
										</div>
										<SkeletonBox className="dash-skeleton-title" />
										<div className="dash-history-bottomline">
											<SkeletonBox className="dash-skeleton-metric" />
											<SkeletonBox className="dash-skeleton-meta" />
										</div>
									</div>
									<SkeletonBox className="dash-skeleton-link" />
								</div>
							))}
						</div>
					</section>
				</div>

				<div className="dash-insights-column">
					<section className="dash-grid-cards dash-grid-cards-side">
						{Array.from({ length: 2 }).map((_, index) => (
							<article key={index} className="dash-card dash-card-skeleton" aria-hidden="true">
								<SkeletonBox className="dash-skeleton-card-label" />
								<SkeletonBox className="dash-skeleton-card-value" />
								<SkeletonBox className="dash-skeleton-card-hint" />
							</article>
						))}
					</section>
				</div>
			</section>
		</main>
	);
}
