import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import moment from 'moment';
import {display, toCSV} from './Task.jsx';

export default class TableList extends React.Component {
  constructor(props) {
    super(props)
    this.state = { inventory: false }
  }

  componentWillReceiveProps(newprops) {
    if (this.state.inventory != newprops.inventory) {
      this.setState({inventory: newprops.inventory})
    }
  }

  render() {
    return (
      <div> 
      { Object.keys(this.props.taskGroups).map(function(taskGroupID, i) {
          var taskGroup = this.props.taskGroups[taskGroupID];
          return <Table 
            count={taskGroup.count}
            tasks={taskGroup.tasks} 
            key={taskGroupID} 
            process={this.props.processes[taskGroupID]}
            inventory={this.state.inventory}
            onTaskClick={(t) => this.props.onTaskClick(t)}
          />;
        }, this)
      } 
      </div>
    );
  }
}


function Table(props) {
  return (
    <div className="">
      <TableHeader title={props.process.name} icon={props.process.icon.substr(0,props.process.icon.length-4)}csv={toCSV(props.process, props.tasks)}/>

      <div className="card-container">
        <table>
          <TableHead attributes={props.process.attributes} inventory={props.inventory}/>
          <tbody>
            { props.tasks.map(function(task, i) {
              return <TaskRow onClick={() => props.onTaskClick(task)} task={task} attributes={props.process.attributes} key={task.id} inventory={props.inventory} unit={props.process.unit}/>;
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
      <img src={window.location.origin + "/static/dashboard/img/" + props.icon + "@3x.png"} style={{height:"20px", verticalAlign: "text-bottom", display: "inline-block", marginRight: "8px"}}/>
      <h1 style={{display: "inline-block"}}>{props.title}</h1>
      <a href={'data:application/csv;charset=utf-8,' + encodeURIComponent(props.csv)} download={props.title + ".csv"}><i className="material-icons">file_download</i></a>
    </div>
  );
}

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

  var inputs = <td className={possiblyEmpty(props.task.inputs.length)}>{props.task.inputs.length + " items"}</td>
  if (props.inventory) {
    inputs = false
  }
  return (
    <tr className="" onClick={() => props.onClick()}>
     <td>{display(props.task)}</td>
     <td className={possiblyEmpty(props.task.items.length)}>{props.task.items.length + " " + getUnit(props.unit, props.task.items.length)}</td>
     {inputs}
     { props.attributes.map(function(attribute, i) {
              return <td key={attribute.id}
                className={possiblyEmpty(getAttributeValue(props.task, attribute.id))}>{getAttributeValue(props.task, attribute.id)}</td>
      })}
     <td>{moment(props.task.created_at).format("MM/DD/YY").toString()}</td>
    </tr>
  );
}

function getUnit(unit, count) {
  if(count == 1) {
    return unit
  }
  return unit + "s"
}

function TableHead(props) {
  var inputs = <td>Inputs</td>
  if (props.inventory) {
    inputs = false
  }
  return (
    <thead className=""><tr>
      <td>Task</td>
      <td>Outputs</td>
      {inputs}
       { props.attributes.map(function(attribute, i) {
              return <td key={attribute.id}>{attribute.name}</td>
        })}
       <td>Created on</td>
    </tr></thead>
  );
}