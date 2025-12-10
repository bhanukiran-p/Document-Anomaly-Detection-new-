# Frontend Structure Explanation

## 📁 Overview

The frontend has been **modularized** from large single-file components (1500-2100 lines each) into organized, focused modules. Here's how it works:

---

## 🔄 Before vs After

### ❌ OLD Structure (Before Modularization)
```
Frontend/src/components/
├── MoneyOrderInsights.jsx        (1390 lines - EVERYTHING in one file)
├── CheckInsights.jsx             (1534 lines - EVERYTHING in one file)
├── BankStatementInsights.jsx     (1571 lines - EVERYTHING in one file)
└── PaystubInsights.jsx           (2164 lines - EVERYTHING in one file)
```

**Problem:** Each file contained:
- Data processing logic
- API calls
- Filter components
- Chart components
- Metrics/KPI displays
- State management
- All mixed together = hard to maintain!

---

### ✅ NEW Structure (After Modularization)
```
Frontend/src/components/
├── MoneyOrderInsights/              ← Directory (not a file!)
│   ├── index.jsx                   ← Main container (~100 lines)
│   ├── MoneyOrderDataProcessor.js  ← Data processing (~300 lines)
│   ├── MoneyOrderFilters.jsx       ← Filter UI (~200 lines)
│   ├── MoneyOrderCharts.jsx        ← All charts (~400 lines)
│   ├── MoneyOrderMetrics.jsx       ← KPI cards (~150 lines)
│   └── hooks/
│       └── useMoneyOrderData.js    ← Data fetching hook (~200 lines)
│
├── CheckInsights/                  ← Same structure
│   ├── index.jsx
│   ├── CheckDataProcessor.js
│   ├── CheckFilters.jsx
│   ├── CheckCharts.jsx
│   ├── CheckMetrics.jsx
│   └── hooks/
│       └── useCheckData.js
│
├── BankStatementInsights/          ← Same structure
│   └── ...
│
└── PaystubInsights/                ← Same structure
    └── ...
```

**Benefits:** Each file has ONE clear responsibility!

---

## 🎯 How Each Module Works

### 1. **index.jsx** (Main Container)
**Purpose:** Orchestrates everything - the "conductor" of the component

**What it does:**
- Imports all sub-components
- Uses the custom hook to get data
- Passes props to Filters, Metrics, and Charts
- Handles top-level state (like `activePieIndex` for chart interactions)

**Example:**
```jsx
// MoneyOrderInsights/index.jsx
import { useMoneyOrderData } from './hooks/useMoneyOrderData';
import MoneyOrderFilters from './MoneyOrderFilters';
import MoneyOrderMetrics from './MoneyOrderMetrics';
import MoneyOrderCharts from './MoneyOrderCharts';

const MoneyOrderInsights = () => {
  const { csvData, searchQuery, setSearchQuery, ... } = useMoneyOrderData();
  
  return (
    <>
      <MoneyOrderFilters searchQuery={searchQuery} setSearchQuery={setSearchQuery} />
      <MoneyOrderMetrics csvData={csvData} />
      <MoneyOrderCharts csvData={csvData} />
    </>
  );
};
```

---

### 2. **hooks/use*Data.js** (Custom Hook)
**Purpose:** Handles ALL data-related logic

**What it does:**
- Fetches data from API
- Handles CSV file uploads
- Manages filter states (search, date, employer, etc.)
- Processes and filters data
- Returns everything needed by other components

**Example:**
```jsx
// hooks/useMoneyOrderData.js
export const useMoneyOrderData = () => {
  const [csvData, setCsvData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // API fetching logic
  // CSV upload logic
  // Filter logic
  
  return {
    csvData,
    searchQuery,
    setSearchQuery,
    // ... all other state and functions
  };
};
```

---

### 3. ***DataProcessor.js** (Data Processing)
**Purpose:** Pure functions for transforming raw data

**What it does:**
- Parses CSV files
- Converts strings to numbers
- Calculates statistics (averages, counts, distributions)
- Formats data for charts
- NO React hooks, NO UI - just pure functions!

**Example:**
```jsx
// MoneyOrderDataProcessor.js
export const parseCSV = (text) => {
  // CSV parsing logic
};

export const processData = (rows, selectedIssuer = null) => {
  // Calculate risk distributions
  // Group by issuer
  // Calculate averages
  return {
    riskDistribution: [...],
    recommendationData: [...],
    // ... processed data
  };
};
```

---

### 4. ***Filters.jsx** (Filter Components)
**Purpose:** UI for filtering/searching data

**What it does:**
- Search input field
- Date filter buttons (Last 30 days, etc.)
- Dropdown filters (Employer, Bank, Issuer, etc.)
- Custom date range picker
- Reset filters button

**Example:**
```jsx
// MoneyOrderFilters.jsx
const MoneyOrderFilters = ({ searchQuery, setSearchQuery, issuerFilter, setIssuerFilter, ... }) => {
  return (
    <div>
      <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
      <select value={issuerFilter} onChange={(e) => setIssuerFilter(e.target.value)}>
        {/* options */}
      </select>
    </div>
  );
};
```

---

### 5. ***Metrics.jsx** (KPI Cards)
**Purpose:** Displays summary statistics

**What it does:**
- Shows Total Count
- Shows Average Risk Score
- Shows Approve/Reject/Escalate counts
- Shows High-Risk count
- Beautiful card-based UI

**Example:**
```jsx
// MoneyOrderMetrics.jsx
const MoneyOrderMetrics = ({ csvData, primary }) => {
  return (
    <div>
      <Card>Total: {csvData.total}</Card>
      <Card>Avg Risk: {csvData.avgRisk}%</Card>
      {/* ... more cards */}
    </div>
  );
};
```

---

### 6. ***Charts.jsx** (Visualizations)
**Purpose:** All chart rendering using Recharts

**What it does:**
- Pie charts (AI Decision breakdown)
- Bar charts (Risk distribution)
- Line charts (Trends over time)
- Area charts
- Scatter plots
- Custom tooltips and interactions

**Example:**
```jsx
// MoneyOrderCharts.jsx
import { PieChart, BarChart, LineChart } from 'recharts';

const MoneyOrderCharts = ({ csvData, primary }) => {
  return (
    <div>
      <PieChart data={csvData.recommendationData} />
      <BarChart data={csvData.riskDistribution} />
      {/* ... more charts */}
    </div>
  );
};
```

---

## 🔗 How Imports Work

### Importing from Pages
When a page imports an Insights component, it imports from the **directory**, which automatically resolves to `index.jsx`:

```jsx
// pages/MoneyOrderAnalysis.jsx
import MoneyOrderInsights from '../components/MoneyOrderInsights';
// ↑ This automatically imports from MoneyOrderInsights/index.jsx
```

### Internal Imports (Within a Component)
Within the modularized component, files import from each other:

```jsx
// MoneyOrderInsights/index.jsx
import { useMoneyOrderData } from './hooks/useMoneyOrderData';  // ← Relative path
import MoneyOrderFilters from './MoneyOrderFilters';            // ← Same directory
import { processData } from './MoneyOrderDataProcessor';        // ← Same directory
```

---

## 📊 Data Flow

```
1. Page Component (MoneyOrderAnalysis.jsx)
   ↓ imports
2. Main Container (MoneyOrderInsights/index.jsx)
   ↓ uses hook
3. Custom Hook (hooks/useMoneyOrderData.js)
   ↓ calls processor
4. Data Processor (MoneyOrderDataProcessor.js)
   ↓ returns processed data
5. Hook returns data to Container
   ↓ passes as props
6. Sub-components (Filters, Metrics, Charts)
   ↓ render UI
```

---

## 🗂️ Current File Status

### ✅ Active (New Modular Structure)
- `MoneyOrderInsights/index.jsx` ← **USE THIS**
- `CheckInsights/index.jsx` ← **USE THIS**
- `BankStatementInsights/index.jsx` ← **USE THIS**
- `PaystubInsights/index.jsx` ← **USE THIS**

### ⚠️ Old Files (Backups - Can be deleted)
- `MoneyOrderInsights.jsx` ← Old monolithic file (backed up)
- `MoneyOrderInsights.jsx.backup` ← Backup copy
- `CheckInsights.jsx` ← Old monolithic file (backed up)
- `CheckInsights.jsx.backup` ← Backup copy
- `BankStatementInsights.jsx` ← Old monolithic file (backed up)
- `BankStatementInsights.jsx.backup` ← Backup copy
- `PaystubInsights.jsx` ← Old monolithic file (backed up)

**Note:** The old `.jsx` files still exist but are **NOT being used**. All imports point to the new directory structure.

---

## 🎨 Component Hierarchy

```
App.js
└── Routes
    ├── MoneyOrderAnalysis.jsx
    │   └── MoneyOrderInsights/ (directory)
    │       ├── index.jsx (main container)
    │       ├── MoneyOrderFilters.jsx
    │       ├── MoneyOrderMetrics.jsx
    │       ├── MoneyOrderCharts.jsx
    │       ├── MoneyOrderDataProcessor.js
    │       └── hooks/useMoneyOrderData.js
    │
    ├── CheckAnalysis.jsx
    │   └── CheckInsights/ (same structure)
    │
    ├── BankStatementAnalysis.jsx
    │   └── BankStatementInsights/ (same structure)
    │
    └── PaystubAnalysis.jsx
        └── PaystubInsights/ (same structure)
```

---

## 🚀 Benefits of This Structure

1. **Easier to Find Code**: Need to fix a chart? Go to `*Charts.jsx`. Need to change filters? Go to `*Filters.jsx`.

2. **Easier to Test**: Each module can be tested independently.

3. **Easier to Reuse**: Data processor functions can be reused elsewhere.

4. **Easier to Maintain**: Changes to charts don't affect filters, etc.

5. **Better Collaboration**: Multiple developers can work on different modules without conflicts.

6. **Smaller Files**: Instead of 2000-line files, you have 5-6 focused files of 100-400 lines each.

---

## 📝 Quick Reference

| What You Want To Do | File To Edit |
|---------------------|--------------|
| Change how data is fetched | `hooks/use*Data.js` |
| Change CSV parsing | `*DataProcessor.js` |
| Add/remove filters | `*Filters.jsx` |
| Change KPI cards | `*Metrics.jsx` |
| Modify charts | `*Charts.jsx` |
| Change overall layout | `index.jsx` |

---

## ❓ Common Questions

**Q: Why are there both `.jsx` files and directories with the same name?**  
A: The old `.jsx` files are backups. The new structure uses directories with `index.jsx` inside. Imports automatically resolve to `index.jsx`.

**Q: Can I delete the old `.jsx` files?**  
A: Yes! They're backups. But wait until you've tested everything works first.

**Q: How do I add a new chart?**  
A: Edit the `*Charts.jsx` file in the appropriate Insights directory.

**Q: How do I add a new filter?**  
A: Edit the `*Filters.jsx` file and update the hook in `hooks/use*Data.js` to handle the new filter state.

---

## 🎯 Summary

**Old Way:** One giant file with everything mixed together  
**New Way:** Organized modules, each with a single responsibility

The structure is now:
- **Modular** (separate files for separate concerns)
- **Organized** (logical grouping in directories)
- **Maintainable** (easy to find and edit code)
- **Scalable** (easy to add new features)
