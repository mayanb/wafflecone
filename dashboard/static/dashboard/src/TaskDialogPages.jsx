import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import {Dialog} from 'react-toolbox/lib/dialog'
import {Menu} from 'react-toolbox/lib/menu';
import {display, toCSV, icon} from './Task.jsx';
import update from 'immutability-helper';

export default class Ancestors extends React.Component {
  constructor(props) {
    super(props)
    this.refreshList = this.refreshList.bind(this)
    this.state = {ancestors: [], loading: false}
  }

  render() {
    if (this.state.loading) {
      return (
        <div className="taskDialog-body">
            <div className="spinner"></div>
        </div>
      )
    }

    if (this.state.ancestors.length == 0) {
      return (
        <div>
          <p> The items from this task have no ancestors. </p>
        </div>
      )
    }

    return (
      <div className="taskDialog-body">
        {
          this.state.ancestors.map(function (ancestor, i) {
            return <Tasklet key={ancestor.id} {...ancestor} />
          })
        }
      </div>
    )

  }

  componentWillReceiveProps(np) {
    this.refreshList(np)
  }

  componentDidMount() {
    this.refreshList(this.props)
  }

  refreshList(props) {
    let url = window.location.origin + "/ics/tasks/"
    let thisObj = this
    this.setState({loading: true})

    console.log(props.query)

    $.get(url, props.query)
      .done(function (data) {
        data.sort(function (a, b) {
          return parseFloat(a.process_type.x) - parseFloat(b.process_type.x)
        })
        thisObj.setState({ancestors: data})
      })
      .fail(function (data) {
        console.log(data)
      })
      .always(function () {
        thisObj.setState({loading: false})
      })
  }

}

function Tasklet(props) {

  let notes = getNotes(props)

  var obj = false
  if (notes.trim().length > 0) {
    obj = <p>{notes}</p>
  }

  return (
    <div className="tasklet">

      <div>
        <img src={icon(props.process_type.icon)} />
        <h1>{display(props)}</h1>
        <a href={window.location.origin + "/dashboard/"} target="_blank"><i className="material-icons" style={{fontSize: "14px"}}>open_in_new</i></a>
      </div>
      {obj}

    </div>
  )
}

function getNotes(task) {
  var notesID = 0
  for (var attribute of task.attributes) {
    if(attribute.name.toLowerCase().trim() === "notes") {
      notesID = attribute.id
      break;
    }
  }

  for (var attributeVal of task.attribute_values) {
    if(attributeVal.attribute == notesID)
      return attributeVal.value
  }

  return ""
}