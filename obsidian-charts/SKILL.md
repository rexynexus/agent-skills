---
name: obsidian-charts
description: Create and edit charts in Obsidian using the Charts plugin (phibr0/obsidian-charts). Use when working with chart codeblocks, data visualization, bar charts, line charts, pie charts, radar charts, scatter plots, or when the user mentions charts, graphs, or data visualization in Obsidian notes.
---

# Obsidian Charts Skill

This skill enables skills-compatible agents to create and edit valid chart codeblocks for the Obsidian Charts plugin (phibr0/obsidian-charts), which uses Chart.js as its rendering engine.

## Overview

The Charts plugin supports two codeblock formats:
- **`chart`** - YAML syntax with simplified configuration (primary format)
- **`advanced-chart`** - Raw Chart.js JSON configuration for full control

Supported chart types: `bar`, `line`, `pie`, `doughnut`, `radar`, `polarArea`, `scatter`, `bubble`, `sankey`

## Chart Codeblock (YAML)

The standard format uses YAML inside a fenced `chart` code block.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Chart type: `bar`, `line`, `pie`, `doughnut`, `radar`, `polarArea`, `scatter`, `bubble`, `sankey` |
| `labels` | array | Category labels. Not required when using `id` (chart from table). |
| `series` | array | Array of dataset objects. Not required when using `id`. |

### Series Object

```yaml
series:
  - title: "Series Name"    # Legend label (optional but recommended)
    data: [1, 2, 3, 4, 5]   # Array of numbers (required)
```

Any Chart.js dataset property can be added to a series item and will be passed through:

```yaml
series:
  - title: Revenue
    data: [10, 20, 15, 25]
    borderDash: [5, 5]
    pointRadius: 5
```

## Bar Chart

```chart
type: bar
labels: [Q1, Q2, Q3, Q4]
series:
  - title: Revenue
    data: [12000, 19000, 15000, 22000]
  - title: Expenses
    data: [8000, 11000, 9000, 14000]
beginAtZero: true
```

### Horizontal Bar Chart

```chart
type: bar
labels: [Engineering, Sales, Marketing, Support]
series:
  - title: Headcount
    data: [45, 30, 15, 20]
indexAxis: y
beginAtZero: true
```

### Stacked Bar Chart

```chart
type: bar
labels: [Jan, Feb, Mar, Apr]
series:
  - title: Product A
    data: [20, 30, 25, 35]
  - title: Product B
    data: [15, 20, 18, 22]
  - title: Product C
    data: [10, 8, 12, 15]
stacked: true
beginAtZero: true
```

## Line Chart

```chart
type: line
labels: [Mon, Tue, Wed, Thu, Fri]
series:
  - title: Temperature
    data: [18, 22, 19, 24, 21]
tension: 0.3
```

### Area Chart (Filled Line)

```chart
type: line
labels: [Jan, Feb, Mar, Apr, May, Jun]
series:
  - title: Users
    data: [100, 180, 250, 310, 420, 500]
fill: true
tension: 0.4
beginAtZero: true
```

### Stacked Area Chart

```chart
type: line
labels: [Jan, Feb, Mar, Apr]
series:
  - title: Direct
    data: [50, 60, 70, 80]
  - title: Referral
    data: [30, 35, 40, 50]
  - title: Organic
    data: [20, 25, 30, 35]
fill: true
stacked: true
tension: 0.3
```

### Line with Best Fit

```chart
type: line
labels: [1, 2, 3, 4, 5, 6, 7, 8]
series:
  - title: Measurements
    data: [2.1, 4.3, 5.8, 8.2, 9.7, 12.1, 13.5, 16.0]
bestFit: true
bestFitTitle: Linear Trend
bestFitNumber: 0
tension: 0
```

## Pie Chart

```chart
type: pie
labels: [Engineering, Sales, Marketing, Support, Operations]
series:
  - title: Budget
    data: [35, 25, 20, 10, 10]
labelColors: true
width: 40%
```

## Doughnut Chart

```chart
type: doughnut
labels: [Complete, In Progress, Not Started]
series:
  - title: Tasks
    data: [45, 30, 25]
labelColors: true
width: 40%
```

## Radar Chart

```chart
type: radar
labels: [Speed, Reliability, Comfort, Safety, Efficiency]
series:
  - title: Model A
    data: [80, 90, 70, 85, 75]
  - title: Model B
    data: [70, 75, 90, 80, 85]
rMin: 0
rMax: 100
width: 60%
```

## Polar Area Chart

```chart
type: polarArea
labels: [Red, Green, Yellow, Grey, Blue]
series:
  - title: Votes
    data: [11, 16, 7, 3, 14]
labelColors: true
width: 50%
```

## Scatter Chart

Use `advanced-chart` for scatter plots, as they require `{x, y}` data points:

```advanced-chart
{
  "type": "scatter",
  "data": {
    "datasets": [{
      "label": "Measurements",
      "data": [
        {"x": 1, "y": 2.3},
        {"x": 2, "y": 4.1},
        {"x": 3, "y": 5.8},
        {"x": 4, "y": 8.2},
        {"x": 5, "y": 9.5}
      ]
    }]
  },
  "options": {
    "scales": {
      "x": {"title": {"display": true, "text": "X Axis"}},
      "y": {"title": {"display": true, "text": "Y Axis"}}
    }
  }
}
```

## Bubble Chart

Use `advanced-chart` for bubble charts, as they require `{x, y, r}` data points:

```advanced-chart
{
  "type": "bubble",
  "data": {
    "datasets": [{
      "label": "Projects",
      "data": [
        {"x": 20, "y": 30, "r": 15},
        {"x": 40, "y": 10, "r": 10},
        {"x": 30, "y": 22, "r": 20}
      ]
    }]
  }
}
```

## Sankey Chart

```chart
type: sankey
labels: [Oil, Natural Gas, Coal, Fossil Fuels, Electricity, Energy]
series:
  - data:
      - [Oil, 15, Fossil Fuels]
      - [Natural Gas, 20, Fossil Fuels]
      - [Coal, 25, Fossil Fuels]
      - [Fossil Fuels, 50, Energy]
      - [Electricity, 30, Energy]
    priority:
      Oil: 1
      Natural Gas: 2
      Coal: 3
    colorFrom:
      Oil: black
      Coal: gray
    colorTo:
      Fossil Fuels: slategray
      Energy: orange
```

Each data entry is a `[from, flow_value, to]` triplet. Optional per-node properties:
- `priority` - ordering of nodes (lower = higher position)
- `colorFrom` - color of the flow at the source node
- `colorTo` - color of the flow at the destination node

## Mixed Charts

Override `type` at the series level to combine chart types:

```chart
type: bar
labels: [Jan, Feb, Mar, Apr, May, Jun]
series:
  - title: Revenue
    data: [12, 19, 15, 25, 22, 30]
  - title: Trend
    data: [14, 16, 18, 20, 22, 24]
    type: line
    fill: false
    tension: 0.2
beginAtZero: true
```

## Configuration Options

### Sizing and Layout

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `width` | string (CSS) | `"100%"` | Chart container width. Example: `"400px"`, `"40%"` |
| `padding` | number | - | Layout padding around the chart |

### Line/Area Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fill` | boolean | `false` | Fill area under lines |
| `tension` | number (0-1) | `0` | Line smoothing. 0 = straight, 1 = max curve |
| `spanGaps` | boolean | `false` | Connect points across null/missing values |

### Best Fit Line (line charts only)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `bestFit` | boolean | `false` | Add linear regression best-fit line |
| `bestFitTitle` | string | `"Line of Best Fit"` | Legend label for best-fit line |
| `bestFitNumber` | integer | `0` | Index of series to compute best-fit from |

### Axis Configuration (bar and line)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `beginAtZero` | boolean | - | Force axis to start at zero |
| `stacked` | boolean | `false` | Stack bars/areas on both axes |
| `indexAxis` | `"x"` or `"y"` | `"x"` | Set to `"y"` for horizontal bar charts |
| `xTitle` | string | - | X-axis title |
| `yTitle` | string | - | Y-axis title |
| `xMin` | number | - | X-axis minimum value |
| `xMax` | number | - | X-axis maximum value |
| `yMin` | number | - | Y-axis minimum value |
| `yMax` | number | - | Y-axis maximum value |
| `xReverse` | boolean | - | Reverse x-axis direction |
| `yReverse` | boolean | - | Reverse y-axis direction |
| `xDisplay` | boolean | `true` | Show/hide x-axis |
| `yDisplay` | boolean | `true` | Show/hide y-axis |
| `xTickDisplay` | boolean | `true` | Show/hide x-axis tick labels |
| `yTickDisplay` | boolean | `true` | Show/hide y-axis tick labels |
| `xTickPadding` | number | - | Padding for x-axis tick labels |
| `yTickPadding` | number | - | Padding for y-axis tick labels |

### Radar/Polar Area Axis

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `rMin` | number | - | Minimum value for radial axis |
| `rMax` | number | - | Maximum value for radial axis |
| `beginAtZero` | boolean | - | Force radial axis to start at zero |

### Legend

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `legend` | boolean | `true` | Show/hide chart legend |
| `legendPosition` | string | `"top"` | `"top"`, `"bottom"`, `"left"`, `"right"` |

### Colors and Appearance

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `labelColors` | boolean | - | Give each data point a different color from the palette (use for pie/doughnut/polarArea) |
| `transparency` | number (0-1) | `0.25` | Alpha for background fill colors |
| `textColor` | string | CSS `--text-muted` | Override text color for labels/legend |

### Time Axis

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `time` | string | - | Time-based x-axis: `"day"`, `"week"`, `"month"`, `"year"` |

## Chart from Table

Link a chart to a markdown table using a block ID.

### Table with Block ID

```markdown
| Month | Revenue | Expenses |
| ----- | ------- | -------- |
| Jan   | 10000   | 8000     |
| Feb   | 12000   | 9000     |
| Mar   | 15000   | 11000    |
^finance-data
```

### Chart Referencing the Table

```chart
type: bar
id: finance-data
layout: columns
beginAtZero: true
```

### Table Reference Options

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Block ID of the table (without `^`) |
| `layout` | string | `"columns"` (first column = labels) or `"rows"` (first row = labels) |
| `file` | string | Filename without extension, for tables in other notes |
| `select` | array | Show only specific rows/columns: `[Row1, Row3]` |

The chart updates live when the source table changes.

## Advanced Chart (Raw Chart.js)

The `advanced-chart` code block accepts a raw Chart.js configuration object as JSON. This gives full access to all Chart.js options, plugins, scales, and the annotation plugin.

```advanced-chart
{
  "type": "bar",
  "data": {
    "labels": ["Red", "Blue", "Yellow"],
    "datasets": [{
      "label": "Votes",
      "data": [12, 19, 7],
      "backgroundColor": [
        "rgba(255, 99, 132, 0.2)",
        "rgba(54, 162, 235, 0.2)",
        "rgba(255, 206, 86, 0.2)"
      ],
      "borderColor": [
        "rgba(255, 99, 132, 1)",
        "rgba(54, 162, 235, 1)",
        "rgba(255, 206, 86, 1)"
      ],
      "borderWidth": 1
    }]
  },
  "options": {
    "scales": {
      "y": {
        "beginAtZero": true
      }
    },
    "plugins": {
      "legend": {
        "position": "bottom"
      }
    }
  }
}
```

### Advanced Chart with Annotations

The annotation plugin (`chartjs-plugin-annotation`) is pre-registered:

```advanced-chart
{
  "type": "line",
  "data": {
    "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
    "datasets": [{
      "label": "Sales",
      "data": [65, 59, 80, 81, 56],
      "borderColor": "rgb(75, 192, 192)",
      "tension": 0.1
    }]
  },
  "options": {
    "plugins": {
      "annotation": {
        "annotations": {
          "threshold": {
            "type": "line",
            "yMin": 70,
            "yMax": 70,
            "borderColor": "red",
            "borderDash": [5, 5],
            "label": {
              "display": true,
              "content": "Target"
            }
          }
        }
      }
    }
  }
}
```

## Dataview Integration

Use `window.renderChart()` inside a `dataviewjs` block to create charts from vault data:

```dataviewjs
const pages = dv.pages('#project')
const names = pages.map(p => p.file.name).values
const values = pages.map(p => p.score).values

const chartData = {
    type: 'bar',
    data: {
        labels: names,
        datasets: [{
            label: 'Scores',
            data: values,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    }
}
window.renderChart(chartData, this.container)
```

The `chartData` object is a standard Chart.js configuration. Any Chart.js feature is available through this API.

## Default Color Palette

The plugin cycles through these 6 colors by default:

| Index | Color | RGBA |
|-------|-------|------|
| 1 | Red/Pink | `rgba(255, 99, 132, 1)` |
| 2 | Blue | `rgba(54, 162, 235, 1)` |
| 3 | Yellow | `rgba(255, 206, 86, 1)` |
| 4 | Teal | `rgba(75, 192, 192, 1)` |
| 5 | Purple | `rgba(153, 102, 255, 1)` |
| 6 | Orange | `rgba(255, 159, 64, 1)` |

Background colors are generated from border colors using the `transparency` value (default 0.25).

Custom colors can be set via:
- Plugin settings UI
- CSS variables (with `themeable: true` in settings):

```css
:root {
    --chart-color-1: #ff00ff;
    --chart-color-2: rgb(0, 128, 255);
}
```

## Best Practices

- Use `width: 40%` to `60%` for pie, doughnut, radar, and polarArea charts to prevent them from being too large
- Set `labelColors: true` for pie, doughnut, and polarArea so each slice/segment gets a distinct color
- Use `beginAtZero: true` for bar charts unless negative values are expected
- Use `tension: 0.2` to `0.4` for smooth but not overly curved lines
- Use the `chart` YAML format for standard charts; use `advanced-chart` only when you need fine-grained Chart.js control (annotations, custom scales, per-point colors)
- For mixed charts, set the base `type` to the most common series type, then override `type` on individual series
- When referencing tables, prefer `layout: columns` (the more intuitive orientation)

## Complete Examples

### Monthly Performance Dashboard

```chart
type: bar
labels: [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
series:
  - title: Revenue ($k)
    data: [42, 49, 53, 61, 58, 67, 72, 69, 78, 83, 91, 95]
  - title: Target ($k)
    data: [45, 45, 50, 55, 55, 60, 65, 65, 70, 75, 80, 85]
    type: line
    borderDash: [5, 5]
    fill: false
beginAtZero: true
xTitle: Month
yTitle: Revenue ($k)
legendPosition: bottom
```

### Project Status Breakdown

```chart
type: doughnut
labels: [Complete, In Progress, Blocked, Not Started]
series:
  - title: Tasks
    data: [28, 12, 5, 15]
labelColors: true
width: 45%
```

### Skill Assessment Radar

```chart
type: radar
labels: [Communication, Technical, Leadership, Problem Solving, Teamwork, Creativity]
series:
  - title: Self Assessment
    data: [75, 90, 60, 85, 80, 70]
  - title: Peer Review
    data: [80, 85, 70, 80, 90, 65]
rMin: 0
rMax: 100
width: 50%
```

### Weekly Trend with Smoothing

```chart
type: line
labels: [Week 1, Week 2, Week 3, Week 4, Week 5, Week 6, Week 7, Week 8]
series:
  - title: Active Users
    data: [120, 135, 148, 142, 165, 178, 192, 210]
  - title: New Signups
    data: [30, 42, 38, 45, 50, 55, 48, 62]
tension: 0.3
fill: true
beginAtZero: true
yTitle: Count
legendPosition: bottom
```

## References

- [Obsidian Charts Plugin](https://github.com/phibr0/obsidian-charts)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)
- [chartjs-plugin-annotation](https://www.chartjs.org/chartjs-plugin-annotation/latest/)
