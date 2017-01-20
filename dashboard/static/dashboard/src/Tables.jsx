import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';

export function TableList(props) {
  return (
    <div> 
    { Object.keys(props.taskGroups).map(function(taskGroupID, i) {
        var taskGroup = props.taskGroups[taskGroupID];
        return <Table 
          tasks={taskGroup} 
          key={taskGroupID} 
          process={props.processes[taskGroupID]} />;
      })
    } 
    </div>
  );
}




function Table(props) {
  return (
    <div className="card">
      <TableHeader title={props.process.name} />

      <div className="card-container">
        <table>
          <TableHead />
          <tbody>
            { props.tasks.map(function(task, i) {
              return <TaskRow label={task.label} key={task.id} />;
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}

function TableHeader(props) {
  return (
    <div className="toolbar">
      <h1>{props.title}</h1>
    </div>
  );
}

function TaskRow(props) {
  return (
    <tr className="">
     <td>{props.label}</td>
     <td>2 items</td>
     <td>2 items</td>
     <td>Here's some text!</td>
    </tr>
  );
}

function TableHead(props) {
  return (
    <thead className=""><tr>
      <td>Task</td>
      <td>Outputs</td>
      <td>Inputs</td>
      <td>Attribute</td>
    </tr></thead>
  );
}