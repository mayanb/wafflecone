import React from 'react'
import $ from 'jquery'
import {Link} from 'react-router-dom'
import InventoryDetail from './InventoryDetail.jsx'
import { TaskSelect } from './Inputs.jsx'
import {fetch, post} from './APIManager.jsx'
import {display, icon} from './Task.jsx'
import moment from 'moment'
import update from 'immutability-helper'
import {mountQR, printQRs} from './qr.jsx'
import {Dialog} from './Dialog.jsx'

let dialogs = {
  deleteTask: {
    title: "Are you sure you want to delete this task?",
    text: "You can't undo this action.",
    okText: "Yes, I'm sure"
  }
}

export default class Task extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      task: {},
      ancestors: [],
      descendents: [],
      attributes: [],
      loading: true,
      ancestorsLoading: true,
      descendentsLoading: true,
      activeDialog: dialogs.deleteTask,
      showDialog: false,
      qrcode: null,
    }
  }

  componentWillMount() {
    //mountQR()
  }

  componentDidMount() {
    // let q = new QRCode(document.getElementById("qrtest"), {
    //   text: "",
    //   width: 128,
    //   height: 128,
    //   colorDark : "#000000",
    //   colorLight : "#ffffff",
    //   correctLevel : QRCode.CorrectLevel.Q
    // })
    // this.setState({qrcode: q})
    this.getTask()
    this.getAncestors()
    this.getDescendents()
  }

  getTask() {
    if (!this.props.match.params.id) {
      return
    }
    this.setState({loading: true})
    let id = this.props.match.params.id
    let url = window.location.origin + "/ics/tasks/" + id + "/"
    let component = this
    fetch(url, {})
      .done(function (data) {
        let attrs = component.organizeAttributes(data)
        component.setState({task: data, attributes: attrs})
      })
      .always(function () {
        component.setState({loading: false})
      })
  }

  getAncestors() {
    this.setState({ancestorsLoading: true})
    let id = this.props.match.params.id || 0
    let url = window.location.origin + "/ics/tasks/"
    let params = {child: this.props.match.params.id}
    let component = this
    fetch(url, params)
      .done(function (data) {
        component.setState({ancestors : data})
      })
      .always(function (data) {
        component.setState({ancestorsLoading: false})
      })
  }

  getDescendents() {
    this.setState({descendentsLoading: true})
    let id = this.props.match.params.id || 0
    let url = window.location.origin + "/ics/tasks/"
    let params = {parent: this.props.match.params.id}
    let component = this
    fetch(url, params)
      .done(function (data) {
        component.setState({descendents : data})
      })
      .always(function (data) {
        component.setState({descendentsLoading: false})
      })
  }

  markAsUsed(index, id) {
    let component = this
    let url = '/ics/movements/create/'
    let team = window.localStorage.getItem("team") || "1"

    let params = { 
      status: "RC", 
      origin: team, 
      destination: null,  
      notes: "MARK AS USED",
      items: [ {item: `${id}`}] 
    }

    let headers = {
      contentType: 'application/json',
      processData: false,
    }

    post(url, JSON.stringify(params), headers)
      .done(function (data) {
        let newObj = update(component.state.task, {
          items: {
            [index]: {
              $merge: {is_used: true}
            }
          }
        })
        component.setState({task: newObj})
      }).fail(function (req, err) {
        let qr = this.state.task.items[index].item_qr
        alert(`Couldn't mark the item with QR ${qr.substring(qr.length-6)} as used. :( \n ${err}`)
      })
  }

  printQR(index, id) {
    let qr = this.state.task.items[index].item_qr
    printQRs([qr], this.state.qr)
  }

  handleSearch(val) {
    console.log(val)
    if (val.value && val.value != parseInt(this.props.match.params.id)) {
      console.log("yay")
      window.location.href = window.location.origin + "/dashboard/task/" + val.value
    }
  }

  organizeAttributes(taskData) {
    let attributes = taskData.process_type.attributes
    let values = taskData.attribute_values
    let organized = [
      {attribute: -1, value: taskData.process_type.name, name: "Process", editable: false},
      {attribute: -1, value: taskData.product_type.name, name: "Product", editable: false},
      {attribute: -1, value: taskData.process_type.created_by_name, name: "Production Team", editable: false},
      {attribute: -1, value: moment(taskData.created_at).format('MM/DD/YY h:mm a'), name: "Created at", editable: false},
      {attribute: -1, value: moment(taskData.updated_at).format('MM/DD/YY h:mm a'), name: "Updated at", editable: false},
    ]

    attributes.map(function (attr, i) {
      let val = values.find(function (e) {
        return (e.attribute == attr.id)
      })
      organized.push({attribute: attr.id, value: val?val.value:"", name: attr.name, editable: true})
    })

    organized.push({attribute: -1, value: pl(taskData.inputs.length, taskData.inputUnit), name: "# INPUTS", editable: false})
    organized.push({attribute: -1, value: pl(taskData.items.length, taskData.process_type.unit), name: "# OUTPUTS", editable: false})

    return organized
  }

  render() {
    if (!this.state.task || !Object.values(this.state.task).length) {
      return (
        <div className="task-detail">
          <TaskSelect placeholder="Search for a task" onChange={this.handleSearch.bind(this)} />
        </div>
      )
    }

    var dialog = false;
    if(this.state.showDialog) {
      dialog = <Dialog {...this.state.activeDialog} />
    }

    return (
      <div className="task-detail">
        {dialog}
        <TaskSelect placeholder="Search for a task" onChange={this.handleSearch.bind(this)} />
        <div className="task-header">
          <div className="header-left">
            <img src={icon(this.state.task.process_type.icon)} />
            <span>{this.state.task.display}</span>
          </div>
          <span>{moment(this.state.task.created_at).format('dddd, MMMM Do YYYY, h:mm a')}</span>
        </div>
        <div className="task-content">
          <div>
            <InformationTable attributes={this.state.attributes} />
            <button className="task_button" onClick={() => this.showDialog(dialogs.deleteTask, this.closeTask)}>Close Task</button>
            <button className="task_button">Toggle flag</button>
            <button className="task_button">Delete Task</button>
          </div>
          <div>
            <InputTable inputs={this.state.task.inputs}/>
            <OutputTable outputs={this.state.task.items} onMark={this.markAsUsed.bind(this)}/>
            <TaskTable title="Ancestors" tasks={this.state.ancestors} loading={this.state.ancestorsLoading}/>
            <TaskTable title="Descendents" tasks={this.state.descendents} loading={this.state.descendentsLoading}/>
          </div>
        </div>
      </div>
    )
  }
}

function TaskTable(props) {
  return (
    <Table title={props.title}>
    {
      props.tasks.map(function (task, i) {
        return (
          <a 
            href={window.location.origin + "/dashboard/task/" + task.id} 
            target="_blank" key={i} 
            className="task-attribute-table-row input-table-row"
          >
            <span className="task-row-header">
            <img src={icon(task.process_type.icon)} />
            {task.display}
            <i className="material-icons expand-i">open_in_new</i>
            </span>
            <span className=""></span>
          </a>
        )
      })
    }
    </Table>
  )
}

function InformationTable(props) {
  return (
    <Table>
    {
      props.attributes.map(function(attr, i) {
        let isEmpty = (attr.value == "")
        return (
          <div key={i} className="task-attribute-table-row">
            <span className="information-table-title">{attr.name}</span>
            <span className={"information-table-answer " + (isEmpty?"empty-answer":"")}>{isEmpty?"n/a":attr.value}</span>
          </div>
        )
      })
    }
    </Table>
  )
}

function OutputTable(props) {
  let team = window.localStorage.getItem("team") || "1"
  return (
    <Table title={`Outputs (${(props.outputs || []).length})`}>
    {
      (props.outputs || []).map(function (item, i) {
        let isInInventory = (!item.is_used && item.inventory && item.inventory.toString() == team)
        var inventory = false
        var markAsUsed = false
        if (isInInventory) {
          inventory = <span className="items-inventory"><div className="inv-circle"></div>Inventory</span>
          markAsUsed = <button className="small-mark-button" onClick={() => props.onMark(i, item.id)} >MARK AS USED</button>
        }
        return (
          <div key={item.id} className="task-attribute-table-row output-table-row">
            <span className="items-qr">
              <i className="material-icons">select_all</i>
              {subs(item.item_qr)}
              <button style={{display: "none"}}className="small-print-button">PRINT</button>
              {markAsUsed}
            </span>
            <span className="items-inventory">{inventory}</span>
          </div>
        )
      })
    }
    </Table>
  )
}

function InputTable(props) {
  let grouped = {};
  (props.inputs || []).map(function (input, i) {
    if (grouped[input.input_task]) {
      grouped[input.input_task].push(input)
    } else {
      grouped[input.input_task] = [input]
    }
  })
  return (
    <Table title={`Inputs (${(props.inputs || []).length})`}>
    {
      Object.values(grouped).map(function (group, i) {
        return (
            <a href={window.location.origin + "/dashboard/task/" + group[0].input_task} 
              target="_blank" key={i} 
              className="task-attribute-table-row input-table-row"
            >
              <span>
                {group[0].input_task_display}
                <i className="material-icons expand-i">open_in_new</i>
              </span>
              <span className="input-count">{pl(group.length, "item")}</span>
            </a>
        )
      })
    }
    </Table>
  )
}

function subs(qr) {
  return qr.substring(qr.length-6)
}

function Table(props) {
  let inside = (
    <div className="task-attribute-table-row zero-state zero-state-clean"> <span> Nothing to show here ¯ \_(ツ)_/¯ </span></div>
  )
  if (props.children) {
    inside = props.children
  }

  let header = false
  if (props.title) {
    header = (
      <div className="task-attribute-table-row task-attribute-table-row-header">
        <span>{props.title}</span>
        <span />
      </div>
    )
  }

  return (
    <div className="task-attribute-table">
      {header}
      {inside}
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