import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import moment from 'moment';
import {display, getNotes, toCSV, icon} from './Task.jsx';

export default class ActivityLog extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    if (this.props.tasks) {
      return (

        <div>

          <div className="log-header">
            <span>{[this.props.tasks.length, " ", "result", this.props.tasks.length==1?"":"s"].join("")}</span>
          </div>

          <div> 
            { this.props.tasks.map(function(task, i) {
                return <LogRow key={task.id} {...task} onClick={this.props.onTaskClick}/>
              }, this)
            } 
          </div>
        </div>
      )
    }

    return null;
  }

}

function LogRow(props) {
  console.log(props)
  return (
    <div className="logrow" onClick={() => props.onClick(props)}>
      <div className="first">
        <img className="icon-img" src={icon(props.process_type.icon)} />
      </div>

      <div className="second">
        <div className="header">
          <span className="title">{display(props)}</span>
          <span className="count">{getCount(props)}</span>
        </div>
        <div className="detail">
          <span className="notes">{getNotes(props)}</span>
        </div>
      </div>

      <div className="third">
        <div className="circle"></div>
        <span className="open">OPEN</span>
      </div>
    </div>
  )
}

function getCount(props) {
  let arr = [props.items.length, " ", props.process_type.unit, (props.items.length==1?"":"s")]
  return arr.join("")
}