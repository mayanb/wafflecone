import React from 'react';
import ReactDOM from 'react-dom';
import moment from 'moment';
import {Dialog} from 'react-toolbox/lib/dialog'
import {display, toCSV} from './Task.jsx';

export default function TaskDialog(props) {
  let actions = [
    { label: "Cancel", onClick: props.onTaskClose },
    { label: "Save", onClick: props.onTaskSave }
  ]

  return (
    <Dialog
      actions={actions}
      active={props.active}
      onEscKeyDown={props.onTaskClose}
      onOverlayClick={props.onTaskClose}
      title={""}
    >
      <DialogContents task={props.task} />
    </Dialog>
  )

}

class DialogContents extends React.Component {
  constructor(props) {
    super(props)
    this.onAttributeChange = this.onAttributeChange.bind(this)
    this.state = { attributes: {}}
  }

  onAttributeChange(dsada) {

  }

  componentWillMount() {
    this.setUpAttributes(this.props.task)
  }

  componentWillReceiveProps(np) {
    this.setUpAttributes(np.task)
  }

  setUpAttributes(task) {
    var stateAttributes = {}
    console.log(task.attributes)
    if(task) {
      task.attributes.map(function(attr, i) {
        stateAttributes[attr.id] = getAttributeValue(task, attr.id)
      })
    }
    this.setState({attributes: stateAttributes})
  }

  render() { 
    let props = this.props
    console.log(this.state.attributes)

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
      <div className="taskDialog">

      <div className="taskDialog-header">
        <img src={img(props.task.process_type.icon)} style={{display: "inline-block", height: "24px", marginRight: "8px", verticalAlign: "text-bottom"}}/>
        <h6 style={{display: "inline-block"}}>
          {display(props.task)}
          {obj}
        </h6>
      </div>
        <p className="dialogItem"><span>Product Type</span>{` ${props.task.product_type.name}`}</p>
        <p className="dialogItem"><span>Process Type</span>{` ${props.task.process_type.name}`}</p>
        <p className="dialogItem"><span>Created at</span>{` ${moment(props.task.created_at).format("dddd, MMMM Do YYYY, h:mm a").toString()}`}</p>
        <div className="attribute">
                <span>Custom Display</span>
                <input type="text" value={props.task.custom_display.trim()} onChange={(val) => this.onAttributeChange()} placeholder="eg. R-CVB-0217"/>
              </div>
        <h5>Attributes</h5>
        {
          props.task.attributes.map(function (attr, i) {
            var val = this.state.attributes[attr.id]
            return (
              <div className="attribute" key={attr.id}>
                <span>{attr.name}</span>
                <input type="text" value={val?val.value:""} onChange={(val) => this.onAttributeChange(attr.id, val)} placeholder="blah blah"/>
              </div>
            )
          }, this)
        }
      </div>
    )
  }
}

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

function getAttributeValue(task, attributeID) {
  for (var i = 0; i < task.attribute_values.length; i++) {
    if (task.attribute_values[i].attribute == attributeID) 
      return task.attribute_values[i].value
  }
  return "n/a"
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