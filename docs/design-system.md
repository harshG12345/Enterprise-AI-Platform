# Enterprise UI/UX Design System Specification

## 1. Design Principles & Theme Tokens

The **Enterprise AI Platform** UI is built on a clean, high-contrast, data-dense SaaS design system designed for analytical precision and operational clarity.

### Color Palette

| Token | Hex Value | Semantic Usage |
|---|---|---|
| **Primary** | `#2563EB` | Active nav, primary CTAs, selected toggles, accent highlights |
| **Primary Hover** | `#1D4ED8` | Hover state for primary interactive elements |
| **Background (Main)** | `#F8FAFC` | Main application canvas, sub-pages |
| **Sidebar Background** | `#0F172A` | Deep slate sidebar with crisp icon navigation |
| **Card / Surface** | `#FFFFFF` | Content containers, modal sheets, tables |
| **Border** | `#E2E8F0` | Structural dividers, card borders, table grid lines |
| **Text Primary** | `#0F172A` | Headings, key data values, table text |
| **Text Secondary** | `#64748B` | Subheadings, table headers, metadata captions |
| **Text Muted** | `#94A3B8` | Placeholder text, disabled labels |

### Status Tokens

| Status | Hex Code | Background Tint | Meaning |
|---|---|---|---|
| **Success** | `#16A34A` | `#DCFCE7` | Completed training, healthy drift, active production model |
| **Warning** | `#F59E0B` | `#FEF3C7` | Drift warning, resource threshold warning, deprecation |
| **Error** | `#DC2626` | `#FEE2E2` | Training failure, schema mismatch, validation error |
| **Info** | `#0284C7` | `#E0F2FE` | Running tasks, queued jobs, general notices |

---

## 2. Typography & Spatial Grid

- **Font Family**: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Monospace**: `JetBrains Mono, Fira Code, ui-monospace, monospace` (used for IDs, hashes, logs, code, metrics, hyperparameters)
- **Hierarchy**:
  - Page Title: `text-2xl font-bold tracking-tight text-slate-900`
  - Section Header: `text-lg font-semibold text-slate-900`
  - Body Text: `text-sm text-slate-700 leading-normal`
  - Caption / Metadata: `text-xs font-medium text-slate-500`
- **Spacing Unit**: 4px base (`p-1` = 4px, `p-4` = 16px, `p-6` = 24px)
- **Border Radius**: Consistent `rounded-lg` (8px) for cards, dialogs, inputs, and buttons.

---

## 3. Global Dashboard Layout Anatomy

```
+----------------------------------------------------------------------------------------------------+
| [Logo] Enterprise AI Platform              [Search Datasets/Models...]       (Bell) [User: Admin v]|  <- TopBar (64px)
+-----------------------+----------------------------------------------------------------------------+
| [Dashboard]           | Home > Projects > Credit Risk Assessment                                   |  <- Breadcrumbs
| [Projects]            |----------------------------------------------------------------------------+
| [Datasets]            | Credit Risk Assessment                             [+ New Training Run]    |  <- Page Header
| [Training Wizard]     | High-precision binary classification model pipeline                        |
| [Experiments]         +----------------------------------------------------------------------------+
| [Model Registry]      |  [ Overview ]  [ Datasets (3) ]  [ Models (7) ]  [ Predictions ]           |  <- Tabs
| [Predictions]         +----------------------------------------------------------------------------+
| [Drift & Monitoring]  |                                                                            |
| [Audit Logs]          |  [ Total Runs: 42 ]  [ Best F1: 0.941 ]  [ Prod Status: Healthy ]          |  <- Stat Cards
| [Settings]            |                                                                            |
|                       |  +-------------------------------------+ +-------------------------------+ |
|                       |  | Training Loss / F1 Convergence Chart | | Feature Importance Ranking    | |
|                       |  +-------------------------------------+ +-------------------------------+ |
| [v1.0.0 Enterprise]   |                                                                            |
+-----------------------+----------------------------------------------------------------------------+
  Sidebar (250px)                                  Main Content Area (Fluid / Scrollable)
```

---

## 4. Component Library Standard

- **Tables**: Clean border-collapse tables with hover effects, sticky headers, sorted columns with chevron indicators, pagination controls, and empty-state graphics.
- **Charts**: Fully responsive Recharts components with custom tooltips matching the design system (`bg-slate-900 text-white rounded-md text-xs`).
- **Cards**: Flat white containers with 1px border (`border-slate-200`) and subtle shadows (`shadow-sm hover:shadow-md transition-shadow`).
- **Modals & Drawers**: Backdrop blur with accessible Esc/click-outside dismissals, clear Action/Cancel button pairings.
- **Feedback**: Non-blocking toast notifications (Sonner / Toast) with semantic color ribbons.
