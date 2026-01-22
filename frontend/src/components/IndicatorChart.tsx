import ReactECharts from 'echarts-for-react';
import type { DataPoint } from '../types';

interface IndicatorChartProps {
  dataPoints: DataPoint[];
  title?: string;
  unit?: string;
  height?: number;
  mini?: boolean;
}

export const IndicatorChart = ({
  dataPoints,
  title,
  unit = '',
  height = 300,
  mini = false,
}: IndicatorChartProps) => {
  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-gray-500"
      >
        NO DATA AVAILABLE
      </div>
    );
  }

  const sortedData = [...dataPoints].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const dates = sortedData.map((d) =>
    new Date(d.timestamp).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  );
  const values = sortedData.map((d) => d.value);

  const firstValue = values[0];
  const lastValue = values[values.length - 1];
  const isUp = lastValue >= firstValue;
  const trendColor = isUp ? '#00ff88' : '#ff3366';
  const trendColorFaded = isUp ? 'rgba(0, 255, 136, 0.15)' : 'rgba(255, 51, 102, 0.15)';

  const option = {
    backgroundColor: 'transparent',
    title: title && !mini
      ? {
          text: title,
          left: 'center',
          textStyle: {
            fontSize: 14,
            fontWeight: 500,
            color: '#e2e8f0',
            fontFamily: "'JetBrains Mono', monospace",
          },
        }
      : undefined,
    tooltip: mini
      ? undefined
      : {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 15, 25, 0.95)',
          borderColor: 'rgba(0, 255, 136, 0.2)',
          borderWidth: 1,
          textStyle: {
            color: '#e2e8f0',
            fontFamily: "'JetBrains Mono', monospace",
          },
          formatter: (params: unknown[]) => {
            const data = (params as { dataIndex: number; value: number }[])[0];
            const date = new Date(sortedData[data.dataIndex].timestamp);
            const formattedDate = date.toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            });
            return `<span style="color: #00ff88">${formattedDate}</span><br/><span style="color: ${trendColor}; font-size: 16px; font-weight: bold">${data.value.toFixed(2)} ${unit}</span>`;
          },
        },
    grid: {
      left: mini ? 0 : 60,
      right: mini ? 0 : 20,
      top: mini ? 5 : title ? 40 : 20,
      bottom: mini ? 0 : 30,
      containLabel: !mini,
    },
    xAxis: {
      type: 'category',
      data: dates,
      show: !mini,
      axisLine: { lineStyle: { color: 'rgba(0, 255, 136, 0.1)' } },
      axisLabel: {
        color: '#6b7280',
        fontSize: 10,
        fontFamily: "'JetBrains Mono', monospace",
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      show: !mini,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(0, 255, 136, 0.05)' } },
      axisLabel: {
        color: '#6b7280',
        fontSize: 10,
        fontFamily: "'JetBrains Mono', monospace",
        formatter: (value: number) => {
          if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
          }
          return value.toFixed(1);
        },
      },
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: mini ? 'none' : 'circle',
        symbolSize: 4,
        lineStyle: {
          color: trendColor,
          width: mini ? 1.5 : 2,
          shadowColor: trendColor,
          shadowBlur: 10,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: trendColorFaded },
              { offset: 1, color: 'transparent' },
            ],
          },
        },
        itemStyle: {
          color: trendColor,
          borderColor: trendColor,
          shadowColor: trendColor,
          shadowBlur: 8,
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
};
