import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import moment from 'moment';
import {display, getNotes, getOperator, toCSV, icon} from './Task.jsx';

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
            onTaskClick={this.props.onTaskClick}
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
      <TableHeader title={props.process.name} icon={props.process.icon} csv={toCSV(props.process, props.tasks)} count={props.count} unit={props.process.unit}/>

      <div className="card-container">
        <table>
          <TableHead attributes={props.process.attributes} inventory={props.inventory}/>
          <tbody>
            { props.tasks.map(function(task, i) {
              return (<TaskRow 
                onClick={() => props.onTaskClick(task)} 
                task={task}
                attributes={props.process.attributes} 
                key={task.id} 
                inventory={props.inventory} 
                unit={props.process.unit}
              />)
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}

//<a href={'data:application/csv;charset=utf-8,' + encodeURIComponent(props.csv)} download={props.title + ".csv"}><i className="material-icons">file_download</i></a>
function TableHeader(props) {
  return (
    <div className="toolbar">
      <div className="toolbarIcon">
        <img src={icon(props.icon)} style={{height:"16px", verticalAlign: "text-bottom", display: "inline-block", marginRight: "8px"}}/>
      </div>
      <div className="toolbarText">
        <span className="title">{props.title}</span>
        <span className="detail">{`${props.count} ${props.unit}${props.count==1?"":"s"}`}</span>
      </div>
      
    </div>
  );
}

function possiblyEmpty(val) {
  if ($.type(val) === "number" && val == 0)
    return "zero-cell"
  if ($.type(val) === "string" && val == "")
  return "zero-cell"
}

function getAttributeValue(task, attributeID) {
  for (var i = 0; i < task.attribute_values.length; i++) {
    if (task.attribute_values[i].attribute == attributeID && task.attribute_values[i].value) 
      return task.attribute_values[i].value
  }
  return "n/a"
}

function TaskRow(props) {

  var inputs = <td className={possiblyEmpty(props.task.inputs.length)}>{props.task.inputs.length + " items"}</td>
  if (props.inventory) {
    inputs = false
  }

  let notes = getNotes(props.task)
  let operator = getOperator(props.task)

  return (
    <tr className="" onClick={() => props.onClick()}>
      <td><span>{display(props.task)}</span></td>
      <td className={"outputs " + possiblyEmpty(props.task.items.length)}><span>{props.task.items.length + " " + getUnit(props.unit, props.task.items.length)}</span></td>
      <td className={"notes " + possiblyEmpty(notes)}><span>{notes || "n/a"}</span></td>
      <td className={"operator" + possiblyEmpty(operator)}><span>{operator || "n/a"}</span></td>
      <td><span>{moment(props.task.created_at).format("MM/DD/YY").toString()}</span></td>
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
      <td><span>Task</span></td>
      <td className="outputs"><span>Outputs</span></td>
      <td className="notes"><span>Notes</span></td>
      <td className="operator"><span>Operator</span></td>
      <td><span>Created on</span></td>
    </tr></thead>
  );
}