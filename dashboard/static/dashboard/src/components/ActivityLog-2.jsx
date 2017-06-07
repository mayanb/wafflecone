import React from 'react'
import $ from 'jquery'
import {Link} from 'react-router-dom'
import InventoryDetail from './InventoryDetail.jsx'
import { InventoryFilter, Filters } from './Inputs.jsx'
import {fetch, requestID, ZeroState} from './APIManager.jsx'
import Loading from './Loading.jsx'
import update from 'immutability-helper'
import {display} from './Task.jsx'
import moment from 'moment'
import Datepicker from './Datepicker.jsx'
import ReactImageFallback from "react-image-fallback";

var process = {
  process_name: "Roasting",
  runs: 16,
  outputs: 24,
  process_unit: "red bins",
  flagged: 0,
  experimental: 0,
  origins: [
    {id: 1, product_code: "MM", runs: "10", outputs: "10", flagged: "0", experimental: "0"},
    {id: 2, product_code: "BON", runs: "6", outputs: "14", flagged: "0", experimental: "0"},
  ]
}

export default class Activity extends React.Component {
  constructor(props) {
    super(props)
    this.lastRequestID = -1
    this.lastTaskRequestID = -1
    this.state = { 
      dates: {start: moment(new Date()).format("YYYY-MM-DD"), end: moment(new Date()).format("YYYY-MM-DD")},
      processes: {},

      expanded: {process: 0, origin: 0},
      expandedTasks: [],

      loading: true,
      taskLoading: false,
      mini: true
     }
  }

  componentDidMount() {
    this.getActivity(this.state.dates)
  }

  handleDateRangeChange(obj) {
    this.setState({dates: obj})
    this.getActivity(obj)
  }

  render() {

    let contentArea = false
    if (this.state.loading) {
      contentArea =  <Loading />
    } else if (!this.state.processes || Object.values(this.state.processes).length == 0) {
      contentArea = <ZeroState />
    } else {
      contentArea = (
        Object.values(this.state.processes).map(function (process, i) {
          return <Process key={i} dates={this.state.dates} {...process} expandedTasks={this.state.expandedTasks} onClick={this.handleProcessClick.bind(this)} onOriginClick={this.handleOriginClick.bind(this)} expanded={this.state.expanded.process==process.process_id?this.state.expanded:null}/>
        }, this)
      )
    }

    return (
      <div className={`activity page ${this.state.mini?"mini":""}`}>
        <div className="activity-header page-header">
          <h2>Activity Log</h2>
          <div><Datepicker initialDates={this.state.dates} onChange={this.handleDateRangeChange.bind(this)} /></div>
        </div>
        {contentArea}
      </div>
    )
  }

  handleOriginClick(process, origin) {
    if (process == this.state.expanded.process && origin == this.state.expanded.origin) {
      this.setState({expanded: {process: process, origin: -1}})
    } else {
      this.setState({expanded: {process: process, origin: origin}})
      this.getTasks(this.state.processes[process], this.state.processes[process].origins[origin])
    }
  }

  handleProcessClick(process) {
    if (process == this.state.expanded.process) {
      this.setState({expanded: {process: -1, origin: -1}})
    } else {
      this.setState({expanded: {process: process, origin: -1}})
    }
  }

  getTasks(process, origin) {
    let range = this.state.dates
    this.setState({taskLoading: true})
    let processID = process.process_id
    let productID = origin.product_id

    console.log(processID + " " + productID)
    let params = {
      process_type: processID, 
      product_type: productID, 
      start: toUTCString(range.start), 
      end: toUTCString(range.end, true)
    }
    
    let url = window.location.origin + "/ics/activity/detail/"
    let component = this

    let rID = requestID()
    this.lastTaskRequestID = rID

    fetch(url, params)
      .done(function (data) {
        console.log(data)
        if (component.lastTaskRequestID != rID) 
          return
        component.setState({expandedTasks: data})
      }).always(function (data) {
        if (component.lastTaskRequestID != rID)
          return
        component.setState({taskLoading: false})
      })
  }

  getActivity(range) {
    console.log(range)
    this.setState({loading: true})
    let url = window.location.origin + "/ics/activity/"
    let params = {start: toUTCString(range.start), end: toUTCString(range.end, true)}
    let component = this

    let rID = requestID()
    this.lastRequestID = rID

    fetch(url, params)
      .done(function (data) {
        if (component.lastRequestID != rID) 
          return

        component.lastTaskRequestID = -1
        component.setState({
          processes: component.nestProcesses(data), 
          expanded: {process:-1, origin:-1},
          expandedTasks: [],
        })
      }).always(function () {
        if (component.lastRequestID != rID) 
          return
        component.setState({taskLoading: false, loading: false})
      })
  }

  nestProcesses(data) {
    let processes = {}
    for (var s in data) {
      let skew = data[s]
      let pid = skew.process_id
      if(!processes[pid]) {
        processes[pid] = update({}, {$merge: skew})
        processes[pid].origins = []
        processes[pid].runs = 0
        processes[pid].outputs = 0
      }
      processes[pid].runs += parseInt(skew.runs)
      processes[pid].outputs += parseInt(skew.outputs)
      processes[pid].origins.push(skew)
    }
    return processes
  }

}

function Process(props) {
  let origins = false
  if (props.expanded != null) {
    origins = props.origins.map(function (origin, i) {
      return <Origin 
        key={origin.id} 
        {...origin} 
        onClick={() => props.onOriginClick(props.process_id, i)} 
        process_unit={props.process_unit} 
        expanded={props.expanded.origin==i}
        expandedTasks={props.expandedTasks}
      />
    }, this)
  }

  let link = window.location.origin + "/ics/potatoes/?"
  let team = window.localStorage.getItem("team") || "1"
  let downloadURL = `${window.location.origin}/ics/potatoes/?team=${team}&process=${props.process_id}&start=${props.dates.start}&end=${props.dates.end}`

  let button = <a 
    href={downloadURL}
    onClick={(e) => e.stopPropagation()}
  ><i className="material-icons" >file_download</i></a>

  return (
    <div className={ "activity-process " + (props.expanded?"expanded":"")}> 
      <div onClick={() => props.onClick(props.process_id)}>
        <Row className="activity-process-header"
          img={props.process_name.toLowerCase().replace(/\s/g, '')}
          first={props.process_name}
          second={pl(props.runs, "run")}
          third={pl(props.outputs, props.process_unit)}
          fourth={"0 flagged"}
          fifth={"0 experimental"}
          sixth={button}
        />
      </div>
      {origins}
    </div>
  )
}

function Origin(props) {
  var taskList = false
  if (props.expanded) {
    taskList = props.expandedTasks.map(function (task) {
      return <TaskList {...task} process_unit={props.process_unit}/>
    })
  }
  return (
    <div className={props.expanded?"expanded-origin":""}>
      <div onClick={props.onClick}>
        <Row className="process-origin-header"
          icon={props.expanded?"expand_more":"chevron_right"} 
          first={props.product_code}
          second={pl(props.runs, "run")}
          third={pl(props.outputs, props.process_unit)}
          fourth={!props.flagged?"--":props.flagged + " flagged"}
          fifth={!props.experimental?"--":props.experimental + " experimental"}
        />
      </div>
      { taskList }
    </div>
  )
}

function Row(props) {
  var symbol = false 
  if (props.img) {
    let errorImg = `${window.location.origin}/static/dashboard/img/default@3x.png`
    symbol = <ReactImageFallback src={`${window.location.origin}/static/dashboard/img/${props.img}@3x.png`} fallbackImage={errorImg}/>
  } else if (props.icon) {
    symbol = <span><i className="material-icons arrow">{props.icon}</i></span>
  }

  return (
    <div className={"activity-process-row " + props.className} >
      <div className={"min " + (props.img?"img":"")}>
        {symbol}
      </div>
      <div className="process-name">
        <span>{props.first}</span>
      </div>
      <div className="process-runs tiny">
        <span>{props.second}</span>
      </div>
      <div className="process-outputs">
        <span>{props.third}</span>
      </div>
      <div className="process-flagged tiny">
        <span>{props.fourth}</span>
      </div>
      <div className="process-experimental tiny">  
        <span>{props.fifth}</span>
      </div>
      <div className="process-button no">
        <span>{props.sixth}</span>
      </div>
    </div>
  )
}

function TaskList(props) {
  return (
    <div className="task-list">
    <Row className="process-origin-task"
      first={" "}
      second={<a href={window.location.origin + "/dashboard/task/" + props.id} target="_blank">{display(props)}</a>}
      third={pl(props.outputs, props.process_unit)}
      fourth={"--"}
      fifth={"--"}
    />
    </div>
  )
}

function pl(count, unit) {
  if (count) {

  }
  if (count == 1) 
    return count + " " + unit
  return count + " " + unit + "s"
}


function toUTCString(dateString, addOne) {
  var m = moment(dateString + " 00:00:00")

  if (addOne) {
    m.add(24, "hours")
  }

  return m.utc().format('YYYY-MM-DD-HH-mm-ss-SSSSSS')
}