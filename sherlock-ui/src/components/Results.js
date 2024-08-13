import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

//results component, takes metrics prop
function Results({ metrics }) {
  const COLORS = ['#3e98c7', '#3ec76e', '#c73e3e'];

  //function to render individual metric data
  const renderMetric = (metricKey, metricData) => {
    //map over the entries of metric data, create a list of div elements
    const data = Object.entries(metricData).map(([key, value], index) => (
      //display the progress bar 
      <div key={key} style={{ width: '100px', margin: '10px' }}>
        
        <CircularProgressbar
          value={value * 100}
          text={`${(value * 100).toFixed(1)}%`}
          styles={buildStyles({
            textColor: COLORS[index % COLORS.length],
            pathColor: COLORS[index % COLORS.length],
            trailColor: '#d6d6d6',
          })}
        />
        <div style={{ textAlign: 'center', marginTop: '5px' }}>{key}</div>
      </div>
    ));
    //return function showing key and its data
    return (
      <div key={metricKey}>
        <h4>{metricKey}</h4>
        <div style={{ display: 'flex', justifyContent: 'center' }}>{data}</div>
      </div>
    );
  };
  const renderMetrics = (metrics) => {
    // Sort the values based on order extracted from the keys

    return Object.entries(metrics).map(([key, value]) => {
      const sortedValues = Object.entries(value).sort((a, b) => {
        const aOrder = parseInt(a[0].split('@')[1]);
        const bOrder = parseInt(b[0].split('@')[1]);
        return aOrder - bOrder;
      });
      const sortedValueObject = Object.fromEntries(sortedValues);

      //render metric using render metric function
      return (
        <div key={key}>
          {renderMetric(key, sortedValueObject)}
        </div>
      );
    });
  };

  return (
    <div>
      <h2>Results</h2>
      {metrics ? renderMetrics(metrics) : <p>No metrics to display</p>}
    </div>
  );
}

export default Results;
