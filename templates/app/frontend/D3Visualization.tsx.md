# `frontend/src/components/visualizations/StatusChart.tsx`

See also:

- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [Landing.tsx.md](Landing.tsx.md)

Use this pattern for project-specific charts or graphs. It follows the same
split this playbook expects: React owns the data flow, D3 owns the SVG
drawing.

Install dependency:

```bash
npm install d3
```

Minimal component shape:

```tsx
import * as d3 from "d3";
import { useEffect, useRef } from "react";

type Datum = {
  label: string;
  value: number;
};

export default function StatusChart({ data }: { data: Datum[] }) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) {
      return;
    }

    const width = 720;
    const height = 320;
    const margin = { top: 24, right: 24, bottom: 40, left: 48 };

    const svg = d3.select(svgRef.current).attr("width", width).attr("height", height);
    svg.selectAll("*").remove();

    const x = d3
      .scaleBand()
      .domain(data.map((item) => item.label))
      .range([margin.left, width - margin.right])
      .padding(0.2);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (item) => item.value) ?? 0])
      .nice()
      .range([height - margin.bottom, margin.top]);

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5));

    svg
      .append("g")
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", (item) => x(item.label) ?? 0)
      .attr("y", (item) => y(item.value))
      .attr("width", x.bandwidth())
      .attr("height", (item) => y(0) - y(item.value))
      .attr("fill", "#0f3d57");
  }, [data]);

  return <svg ref={svgRef} role="img" aria-label="Status chart" />;
}
```

Recommended usage:

- parent page fetches records with `useDataProvider()`
- parent page converts API rows into small chart-friendly objects
- D3 component receives plain props and renders the figure

Notes:

- keep D3 components focused and presentational
- clear the SVG before every redraw with `selectAll("*").remove()`
- use MUI around the chart for layout, titles, and filters
- do not fetch API data directly inside a low-level chart component unless
  there is a strong reason
