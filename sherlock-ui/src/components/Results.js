<<<<<<< HEAD
import React from'react';
import { CircularProgressbar, buildStyles } from'react-circular-progressbar';
import'react-circular-progressbar/dist/styles.css';
=======
import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
>>>>>>> db6bebbc3314db13b1d0a359dfda0952ee8d0600

function Results({ metrics }) {
  const COLORS = ['#3e98c7', '#3ec76e', '#c73e3e'];

  const renderMetric = (metricKey, metricData) => {
    const data = Object.entries(metricData).map(([key, value], index) => (
<<<<<<< HEAD
      <div key={key}style={{width: '100px', margin: '10px' }}><CircularProgressbar
=======
      //display the progress bar 
      <div key={key} style={{ width: '100px', margin: '10px' }}>
        
        <CircularProgressbar
>>>>>>> db6bebbc3314db13b1d0a359dfda0952ee8d0600
          value={value * 100}
          text={`${(value * 100).toFixed(1)}%`}
          styles={buildStyles({
            textColor: COLORS[index % COLORS.length],
            pathColor: COLORS[index % COLORS.length],
            trailColor: '#d6d6d6',
          })}
        /><div style={{ textAlign: 'center', marginTop: '5px' }}>{key}</div></div>
    ));
<<<<<<< HEAD

=======
    //return function showing key and its data
>>>>>>> db6bebbc3314db13b1d0a359dfda0952ee8d0600
    return (
      <div key={metricKey}><h4>{metricKey}</h4><div style={{ display: 'flex', justifyContent: 'center' }}>{data}</div></div>
    );
  };
<<<<<<< HEAD

=======
>>>>>>> db6bebbc3314db13b1d0a359dfda0952ee8d0600
  const renderMetrics = (metrics) => {
    return metrics.map((metricObject, index) => (
      <div key={index}style={{marginBottom: '20px' }}><h3>Query {index + 1}</h3>
        {Object.entries(metricObject).map(([key, value]) => {
          const sortedValues = Object.entries(value).sort((a, b) => {
            const aOrder = parseInt(a[0].split('@')[1], 10);
            const bOrder = parseInt(b[0].split('@')[1], 10);
            return aOrder - bOrder;
          });

<<<<<<< HEAD
          const sortedValueObject = Object.fromEntries(sortedValues);
=======
    return Object.entries(metrics).map(([key, value]) => {
      const sortedValues = Object.entries(value).sort((a, b) => {
        const aOrder = parseInt(a[0].split('@')[1]);
        const bOrder = parseInt(b[0].split('@')[1]);
        return aOrder - bOrder;
      });
      const sortedValueObject = Object.fromEntries(sortedValues);
>>>>>>> db6bebbc3314db13b1d0a359dfda0952ee8d0600

          return <div key={key}>{renderMetric(key, sortedValueObject)}</div>;
        })}
      </div>
    ));
  };

  return (
    <div><h2>Results</h2>
      {metrics && metrics.length > 0 ? renderMetrics(metrics) : <p>No metrics to display</p>}
    </div>
  );
}

export default Results;
