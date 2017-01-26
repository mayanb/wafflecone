import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import moment from 'moment';
import {display, toCSV} from './Task.jsx';

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
      <TableHeader title={props.process.name} csv={toCSV(props.process, props.tasks)}/>

      <div className="card-container">
        <table>
          <TableHead attributes={props.process.attributes}/>
          <tbody>
            { props.tasks.map(function(task, i) {
              return <TaskRow task={task} attributes={props.process.attributes} key={task.id} />;
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
      <a href={'data:application/csv;charset=utf-8,' + encodeURIComponent(props.csv)} download={props.title + ".csv"}><i className="material-icons">file_download</i></a>
    </div>
  );
}

// function display(task) {
//   if (task.custom_display && task.custom_display != "") 
//     return task.custom_display
//   else if (task.label_index > 0)
//     return task.label + "-" + task.label_index
//   else
//     return task.label
// }

function possiblyEmpty(val) {
  if ($.type(val) === "number" && val == 0)
    return "zero-cell"
  if ($.type(val) === "string" && val == "n/a")
  return "zero-cell"
}

function getAttributeValue(task, attributeID) {
  for (var i = 0; i < task.attribute_values.length; i++) {
    if (task.attribute_values[i].attribute == attributeID) 
      return task.attribute_values[i].value
  }
  return "n/a"
}

function TaskRow(props) {
  return (
    <tr className="">
     <td>{display(props.task)}</td>
     <td className={possiblyEmpty(props.task.items.length)}>{props.task.items.length + " items"}</td>
     <td className={possiblyEmpty(props.task.inputs.length)}>{props.task.inputs.length + " items"}</td>
     { props.attributes.map(function(attribute, i) {
              return <td key={attribute.id}
                className={possiblyEmpty(getAttributeValue(props.task, attribute.id))}>{getAttributeValue(props.task, attribute.id)}</td>
      })}
     <td>{moment(props.task.created_at).format("MM/DD/YY").toString()}</td>
    </tr>
  );
}

function TableHead(props) {
  return (
    <thead className=""><tr>
      <td>Task</td>
      <td>Outputs</td>
      <td>Inputs</td>
       { props.attributes.map(function(attribute, i) {
              return <td key={attribute.id}>{attribute.name}</td>
        })}
       <td>Created on</td>
    </tr></thead>
  );
}