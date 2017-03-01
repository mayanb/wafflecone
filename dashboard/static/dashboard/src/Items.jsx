import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';
import {Dialog} from 'react-toolbox/lib/dialog'
import {Menu} from 'react-toolbox/lib/menu';
import {display, toCSV, icon} from './Task.jsx';
import update from 'immutability-helper';

export default class Items extends React.Component {
  constructor(props) {
    super(props)
    this.refreshList = this.refreshList.bind(this)
    this.handleClick = this.handleClick.bind(this)
    this.state = {items: [], loading: false}
  }

  render() {
    if (this.state.loading) {
      return (
        <div className="taskDialog-body">
            <div className="spinner"></div>
        </div>
      )
    }

    if (this.state.items.length == 0) {
      return (
        <div className="taskDialog-body">
          <p> This task has no items.</p>
        </div>
      )
    }

    return (
      <div className="taskDialog-body">
        {
          this.state.items.map(function (item, i) {
            return <Itemlet key={item.id} onClick={() => this.handleClick(item)} {...item} />
          }, this)
        }
      </div>
    )

  }

  handleClick(item) {
    let thisObj = this
    let url = window.location.origin + "/ics/inputs/create/"

    // 516 is the ID of the deliver to heaven task...probably 
    // need to make this less janky
    let data = {input_item: item.id, task: "573"}

    $.ajax({
      url: url,
      method: "POST",
      data: data
    }).done(function (data) {
      var itemIndex = -1
      thisObj.state.items.map(function (x, i) {
        if (x.id == item.id)
          itemIndex = i
      })
      if (itemIndex == -1) {
        alert("something has gone horribly wrong")
      }

      let ns = update(thisObj.state, { items: {$splice: [[itemIndex, 1]] }})
      thisObj.setState(ns)

    }).fail(function (err) {
      console.log(err)
    }).always(function () {

    })
  }

  componentWillReceiveProps(np) {
    this.refreshList(np)
  }

  componentDidMount() {
    this.refreshList(this.props)
  }

  refreshList(props) {
    this.setState({items: props.task.items})
  }

}

function Itemlet(props) {

  return (
    <div className="tasklet">

      <div style={{display: "flex", margin: "10px" }}>
        <i className="material-icons" style={{flex:"0 auto", fontSize: "14px"}}>ac_unit</i>
        <h1 style={{flex: "1 auto"}}>{qrdisplay(props)}</h1>
        <div style={{flex:"0 auto"}}>
          <button onClick={props.onClick}>Send to heaven</button>
        </div>
      </div>
    </div>
  )
}

function qrdisplay(item) {
  return item.item_qr.substring(item.item_qr.length-6, item.item_qr.length)
}