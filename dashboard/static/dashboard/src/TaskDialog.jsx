import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import moment from 'moment';
import {Dialog} from 'react-toolbox/lib/dialog'
import {Menu} from 'react-toolbox/lib/menu';
import {display, toCSV, icon} from './Task.jsx';
import update from 'immutability-helper';
import Ancestors from './TaskDialogPages.jsx'
import Items from './Items.jsx'

export default class TaskDialog extends React.Component {

  constructor(props) {
    super(props)
    this.state = {active: 1}
  }

  componentWillReceiveProps(np) {
    this.setState({active: 0})
  }

  render() {
    let props = this.props
    var obj

    if (props.task == null) {
      return null
    }

    if (this.state.active == 0) {
      obj = <Details task={props.task} onTaskChanged={props.onTaskChanged}/>
    } else if (this.state.active == 1) {
      obj = <Items task={props.task} />
    } else if (this.state.active == 2) {
      let request1 = {child: props.task.id}
      obj = <Ancestors query={request1} />
    } else if (this.state.active == 3) {
      let request2 = {parent: props.task.id}
      obj = <Ancestors query={request2} />
    }

    var label = props.task.label
    if (props.task.label_index > 0) {
      label = label + "-" + props.task.label_index
    }

    var obj2 = <span>{`(${label})`}</span>
    if (!props.task.custom_display || props.task.custom_display.trim() == "") {
      obj2 = false
    }

    return (
      <Dialog
        actions={[]}
        active={props.active}
        onEscKeyDown={props.onTaskClose}
        onOverlayClick={props.onTaskClose}
        title={""}
      >
        <div className="taskDialog">

          <div className="toolbar">
            <div className="toolbarIcon">
              <img src={icon(props.task.process_type.icon)} style={{height:"20px", verticalAlign: "text-bottom", display: "inline-block", marginRight: "8px"}}/>
            </div>
            <div className="toolbarText">
              <h1>{display(props.task)}{obj2}</h1>
            </div>
          </div>

          <MenuBar options={["Details", "Items", "Ancestors", "Descendents"]} active={this.state.active} onClick={ (val) => this.setState({active: val}) } />

          {obj}

        </div>

      </Dialog>
    )
  }
}

function MenuBar(props) {
  return (
    <div className="menuBar">
      <ul>
      {
        props.options.map(function (option, i) {
          return (<li key={i} className={props.active==i?"activeTab":""}onClick={() => props.onClick(i)}>{option}</li>)
        })
      }
      </ul>
    </div>
  )
}

class Details extends React.Component {
  constructor(props) {
    super(props)
    this.handleAttributeChange = this.handleAttributeChange.bind(this)
    this.handleSave = this.handleSave.bind(this)
    this.handleCancel = this.handleCancel.bind(this)
    this.handleCustomNameChange = this.handleCustomNameChange.bind(this)
    this.handleCustomNameSave = this.handleCustomNameSave.bind(this)
    this.handleCustomNameCancel = this.handleCustomNameCancel.bind(this)
    this.state = { attributes: {}}
  }

  handleCustomNameChange(value) {
    this.setState({newCustomName : value.trim()})
  }

  handleCustomNameSave(attributeID, callback) {
    let url = window.location.origin + "/ics/tasks/edit/" + this.props.task.id + "/"
    let thisObj = this

    let data = {
      is_open : this.props.task.is_open,
      label: this.props.task.label,
      label_index : this.props.task.label_index,
      custom_display : this.state.newCustomName,
      is_trashed: this.props.task.is_trashed
    }

    if (this.state.newCustomName != undefined) {
      $.ajax({
        method: "PUT",
        url: url,
        data: data
      }).done(function () {
        thisObj.props.onTaskChanged(thisObj.props.task)
        callback()
      }).fail(function (data) {
        console.log(data)
      })
    }
  }

  handleCustomNameCancel() {
    this.setState({newCustomName: undefined})
  }

  handleAttributeChange(attributeID, value) {
    let attribute = this.state.attributes[attributeID]
    let ns = update(this.state, {
      attributes: {
        [attributeID] : {
          $merge: {newValue: value}
        }
      }
    })
    this.setState(ns)
  }

  handleCancel(attributeID) {
    let attribute = this.state.attributes[attributeID]
    let old = attribute.value
    let ns = update(this.state, {
      attributes: {
        [attributeID] : {
          $merge: {newValue: undefined}
        }
      }
    })
    this.setState(ns)
  }

  handleSave(attributeID, callback) {
    let url = window.location.origin + "/ics/taskAttributes/"
    let attribute = this.state.attributes[attributeID]
    let thisObj = this

    if (attribute.id != -1 && attribute.newValue != undefined) {
      $.ajax({
        method: "PUT", 
        url: url + attributeID + "/",
        data: {attribute: attributeID, value: attribute.newValue.trim(), task: this.props.task.id}
      }).done(function (data) {
        thisObj.props.onTaskChanged(thisObj.props.task)
        callback()
      }).fail(function (data) {
        console.log(data)
      }).always(function (data) {
      })
    }
  }

  componentWillMount() {
    this.setUpAttributes(this.props.task)
  }

  componentWillReceiveProps(np) {
    this.setUpAttributes(np.task)
  }

  setUpAttributes(task) {
    console.log("setting up attributes")
    var stateAttributes = {}
    console.log(task)
    if(task) {
      task.attributes.map(function(attr, i) {
        stateAttributes[attr.id] = getAttribute(task, attr.id)
      })
    }
    this.setState({attributes: stateAttributes})
  }

  render() { 
    let props = this.props

    if (props.task == null) {
      return false
    }

    let sentence = constructSentence(props.task)
    var label = props.task.label
    if (props.task.label_index > 0) {
      label = label + "-" + props.task.label_index
    }

    let obj = <span>{`(${label})`}</span>

    if (!props.task.custom_display || props.task.custom_display.trim() == "") {
      obj = false
    }

    return (
      <div className="taskDialog-body" style={{overflow: "scroll"}}>
        <Attribute name="Product Type" value={props.task.product_type.name} editable={false} />
        <Attribute name="Process Type" value={props.task.process_type.name} editable={false} />
        <Attribute name="Created at" value={moment(props.task.created_at).format("dddd, MMMM Do YYYY, h:mm a").toString()} editable={false} />
        <Attribute 
          name="Custom Name" 
          newValue={this.state.newCustomName} 
          value={props.task.custom_display.trim()} 
          editable={true} 
          onAttributeChange={(val) => this.handleCustomNameChange(val)}
          onSave={this.handleCustomNameSave}
          onCancel = {this.handleCustomNameCancel}
        />
        {
          props.task.attributes.map(function (attr, i) {
            var val = this.state.attributes[attr.id]
            return (
              <Attribute 
                key={attr.id} 
                id={attr.id}
                name={attr.name} 
                newValue={val.newValue}
                value={val.value}
                onAttributeChange={(val) => this.handleAttributeChange(attr.id, val)}
                onSave={this.handleSave}
                onCancel={this.handleCancel} 
                editable={true}
              />
            )
          }, this)
        }
      </div>
    )
  }
}

class Tooltip extends React.Component {
  constructor(props) {
    super(props)
    this.handleSaveClicked = this.handleSaveClicked.bind(this)
    this.handleMenuHide = this.handleMenuHide.bind(this)
  }

  handleMenuHide() {
    this.props.onCancel(this.props.id)
    this.props.onMenuHide()
  }

  handleSaveClicked() {
    let thisObj = this
    this.props.onSave(this.props.id, function () {
      thisObj.handleMenuHide()
    })
  }

  render() {

    function stopPropagation (e) {
      e.stopPropagation();
    }

    return ( 
      <div style={{position: 'absolute', top: this.props.y, left: this.props.x, padding: "12px" }}>
        <Menu position="auto" active={this.props.active} onHide={this.handleMenuHide}>
          <div className="menuContentWrapper" style={{display: "inline-block"}} onClick={ stopPropagation } >
            <div>
              <span className="attributeTitle">{this.props.name}</span>
            </div>
            <div>
              <input type="text" placeholder="max. 20 chars" value={this.props.value} onChange={(e) => this.props.onAttributeChange(e.target.value) } />
            </div>
            <div>
              <button onClick={() => this.handleSaveClicked()}>Save</button>
              <button onClick={this.handleMenuHide}>Cancel</button>
            </div>
          </div>
        </Menu>
      </div>
    )
  }
}


class Attribute extends React.Component {
  constructor(props) {
    super(props)
    this.handleHover = this.handleHover.bind(this)
    this.handleClick = this.handleClick.bind(this)
    this.state = { hovered: false, tooltip: false}
  }

  handleHover() {
    this.setState({hovered: !this.state.hovered})
  }

  handleClick(e) {
    this.setState({tooltip: !this.state.tooltip, x: e.pageX-100, y: e.pageY-100})
  }

  render () {
    let props = this.props

    var color = "rgb(150,163,182)"

    if (!props.value || props.value.length == 0) {
      color = "rgba(0,0,0,0.25)"
    }

    var editButton = false
    var tooltip = false
    if (props.editable) {
      editButton = (
        <div>
          <i className="material-icons" style={{visibility: this.state.hovered?"visible":"hidden", color: color}}>edit</i>
        </div>)
      tooltip = (
        <Tooltip 
          active={this.state.tooltip} 
          onMenuHide={() => this.setState({tooltip: false})}
          x = {this.state.x}
          y = {this.state.y}
          name= {props.name}
          value={this.props.newValue != undefined ? this.props.newValue:this.props.value}
          onAttributeChange={props.onAttributeChange}
          onSave={props.onSave}
          onCancel={props.onCancel}
          id = {props.id}
        />
      )
    }

    return (
      <div 
      className="attribute" 
      style={{display: "flex"}} 
      onMouseEnter={this.handleHover} 
      onMouseLeave={this.handleHover}
      onClick={this.handleClick}
      >
        <div style={{}}>
          <span className="attributeTitle">{props.name}</span>
        </div>
        <div style={{borderBottom: props.editable?("1px dotted " + color):"none"}}>
          <span className="attributeValue" style={{color: color}}>{props.value.length?props.value:"optional"}</span>
        </div>
        {editButton}
        {tooltip}
      </div>

    )
  }
}

// <input type="text" value={props.value} onChange={(val) => props.onAttributeChange(props.id, val)} placeholder="blah blah"/>

function img(name) {
  let n2 = name.substr(0, name.length-4)
  return window.location.origin + "/static/dashboard/img/" + n2 + "@3x.png"
}

function past(verb) {
  let last = verb.length-1
  if (verb.substr(last) == "e") {
    return verb.substr(0,last) + "ed"
  } else {
    return verb + "ed"
  }
}

function getAttribute(task, attributeID) {
  for (var i = 0; i < task.attribute_values.length; i++) {
    if (task.attribute_values[i].attribute == attributeID) 
      return task.attribute_values[i]
  }
  return { attribute: attributeID, value: "", id: -1}
}

// "2 red bins of Madagascar were winnowed on 2/2/17. 4 grey bins of winnowed product were output."
function constructSentence(task) {
  let processName = task.process_type.name.toLowerCase()
  let productName = task.product_type.name
  let inputUnit = task.inputUnit.toLowerCase()
  let outputUnit = task.process_type.unit.toLowerCase()

  let numInputs = task.inputs.length
  let numOutputs = task.items.length

  let inputPl = (numInputs != 1)
  let outputPl = (numOutputs != 1)
  let date = moment(task.created_at).format("MM/DD/YY").toString()

  // "2 red bins of Madagascar"
  let firstHalf = `${numInputs} ${inputUnit}${inputPl?"s":""} of ${productName} ${inputPl?"were":"was"} ${past(processName)} on ${date}.`

  return firstHalf
}

function getAttributeValue(task, attributeID) {
  for (var i = 0; i < task.attribute_values.length; i++) {
    if (task.attribute_values[i].attribute == attributeID) 
      return task.attribute_values[i]
  }
  return { attribute: attributeID, value: "", id: -1}
}