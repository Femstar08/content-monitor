# AWS Content Monitor - Frontend

A modern React-based web interface for managing AWS content monitoring profiles and viewing intelligence digests.

## Architecture

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS + Headless UI components
- **State Management**: React Query + Zustand
- **Routing**: React Router v6
- **Charts**: Recharts for analytics
- **Forms**: React Hook Form + Zod validation
- **API**: Axios with React Query

## Key Features

### 1. Dashboard

- Overview of all monitoring profiles
- Recent changes summary
- System health metrics
- Quick actions

### 2. Profile Management

- Create/edit/delete monitoring profiles
- Configure inclusion/exclusion rules
- Set scheduling and notification preferences
- Test profile configurations

### 3. Content Discovery

- View discovered sources
- Browse content hierarchy
- Filter and search capabilities
- Source validation status

### 4. Change Detection

- Timeline view of detected changes
- Change classification and impact scoring
- Diff viewer for content changes
- Export capabilities

### 5. Intelligence Digests

- Generated digest viewer
- Multiple format support (HTML, PDF, Text)
- Historical digest archive
- Sharing and distribution

### 6. Analytics

- Content monitoring metrics
- Change frequency analysis
- Source reliability tracking
- Performance dashboards

## Component Structure

```
src/
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── dashboard/          # Dashboard components
│   ├── profiles/           # Profile management
│   ├── content/            # Content viewing
│   ├── changes/            # Change detection UI
│   ├── digests/            # Digest management
│   └── analytics/          # Analytics components
├── hooks/                  # Custom React hooks
├── services/               # API services
├── stores/                 # Zustand stores
├── types/                  # TypeScript types
└── utils/                  # Utility functions
```
