import React from 'react'
import $ from 'jquery'
import {display} from './Task.jsx'
import {fetch, post} from './APIManager.jsx'
import update from 'immutability-helper'
import {Link} from 'react-router-dom'
import Loading from './Loading.jsx'
import {Dropdown} from 'react-toolbox/lib/dropdown'
import {Dialog} from './Dialog.jsx'

export default class InventoryDetail extends React.Component {

  constructor(props) {
    super(props)
    this.latestRequestID = -1
    this.handleLoadClick = this.handleLoadClick.bind(this)
    this.state = { 
      items: [],
      selected: [],
      next: null,
      loading: false,
      selectedCount: 0,
      dialog: false
    }
  }

  componentDidMount() {
    this.getInventoryItems(this.props)
  }

  componentWillReceiveProps(np) {
    this.getInventoryItems(np)
  }

  handleLoadClick() {
    this.getInventoryItems(this.props, this.state.next)
  }


  render() {
    let props = this.props

    var contentArea = <ItemList {...props} items={this.state.items} onChange={this.handleItemSelect.bind(this)} selected={this.state.selected}/>
    if (!this.state.items || this.state.items.length == 0) {
      if (this.state.loading) {
        contentArea = <Loading />
      }
    }

    let loadMore = false
    if (this.state.next) {
      loadMore = <button onClick={this.handleLoadClick}>Load More</button>
    }

    let deliver = false
    if (this.state.selectedCount > 0) {
      deliver = <button onClick={() => this.setState({dialog: true})}>{`Deliver ${this.state.selectedCount} items`}</button> 
    }

    let dialog = false
    if (this.state.dialog) {
      dialog = <DeliveryDialog onCancel={() => this.setState({dialog: false})} onDeliver={this.deliverItems.bind(this)}/>
    }

    return (
      <div className={"inventory-detail " + (props.showDetail?"":"smallDetail")}>
        {dialog}
        <div className="i-detail-header">
          <div className="i-detail-outputdesc" style={{display: "flex", flexDirection: "row"}}>
            <span style={{flex: "1"}}>{this.props.output_desc}</span>
            <span><Link to="/dashboard/inventory/">
              <i style={{verticalAlign: "middle", fontSize: "16px", flex: "0"}} className="material-icons">close</i>
            </Link></span>
          </div>
          <div className="i-detail-count">
            <span>{(this.props.count || 0) + " " + this.props.unit + "s"}</span>
          </div>
        </div>
        <div className="i-detail-content">
          { contentArea }
        </div>
        <div className="i-detail-footer">
          { loadMore }
          { deliver }
        </div>
      </div>
    )
  }

  getInventoryItems(props, u) {
    if (!props.match.params.id) {
      return
    }

    this.setState({loading: true})

    let url = u || window.location.origin + "/ics/inventory/detail/"// + props.match.params.id
    let g = {process: props.process_id}
    if(this.props.filter) {
      g.products = this.props.filter
    }
    let random = Math.floor(Math.random() * 1000)
    this.latestRequestID = random

    let component = this
    fetch(url, g)
      .done(function (data, d, jqxhr) {
        if (component.latestRequestID == random) {
          var items = data.results
          var selected = new Array(items.length).fill(false)
          if(u) {
            items = update(component.state.items, {$push: items})
            selected = update(component.state.selected, {$push: selected})
          }
          component.setState({items: items, next: data.next, selected: selected})
        }
      }).always(function () {
        component.setState({loading: false})
      })
  }

  handleItemSelect(i) {
    let newVal = !this.state.selected[i]

    let newCount = this.state.selectedCount
    if (newVal) {
      newCount =this.state.selectedCount + 1
    } else {
      newCountt = this.state.selectedCount - 1
    }

    console.log(newCount)

    let newArr = update(this.state.selected, {$splice: [[i, 1, newVal]]})
    this.setState({selected: newArr, selectedCount: newCount})
  }

  deliverItems(destination, callback) {
    let items = this.state.items
    let selected = this.state.selected

    let itemsToDeliver = []
    for(let [i, val] of items.entries()) {
      if (selected[i]) {
        itemsToDeliver.push({item: `${val.id}`})
      }
    }

    let team = window.localStorage.getItem("team") || "1"
    let component = this
    let url = '/ics/movements/create/'

    let params = {
      status: "RC", 
      origin: team, 
      destination: destination,  
      notes: "DELIVERED VIA WEB",
      items: itemsToDeliver
    }

    post(url, JSON.stringify(params))
      .done(function (data) {
        if (callback) 
          callback()
        component.getInventoryItems(component.props, null)
        component.setState({selectedCount: 0})
      }).fail(function (req, err) {
        alert(`Couldn't deliver the items. :( \n ${err}`)
      })
  }
}

function ItemList(props) {
  return (
    <div>
    {
      (props.items || []).map(function (item, i) {
        return <Item key={i} i={i} {...item} onChange={props.onChange} selected={props.selected[i]}/>
      }, this)
    }
    </div>
  )
}

function Item(props) {
  let src = window.location.origin + "/static/dashboard/img/qricon@2x.png"
  return (
    <div className="item" onClick={props.onClick}>
      <div className="flex">
        <div className="item-img">
          <img src={src} />
        </div>
        <div>
          <span className="item-qr">{props.item_qr.substring(42)}</span>
          <a href={window.location.origin + "/dashboard/task/" + props.creating_task.id} target="_blank"><span className="item-task">{display(props.creating_task)}</span></a>
        </div>
      </div>
      <div className="unflex">
        <input type="checkbox" value={props.selected} checked={props.selected} onChange={() => props.onChange(props.i)} />
      </div>
    </div>
  )
}

class DeliveryDialog extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      destination: null,
      loading: false,
      done: false
    }
  }

  handleDeliver() {
    this.setState({loading: true})
    let component = this
    this.props.onDeliver(this.state.destination, function () {
      component.setState({done: true})
    })
  }

  render() {
    let teams = [{value: 1, label: "Bama Pirates"}, {value: 5, label: "Valencia Wizards"}, {value: null, label: "Other"}]

    if (this.state.done) {
      return (
        <Dialog>
          <span className="dialog-title">Deliver items</span>
          <span className="dialog-text">Yay! You delivered the items!</span>
          <div className="dialog-actions">
            <button className="dialog-button dialog-cancel" onClick={this.props.onCancel}>OK</button>
          </div>
        </Dialog>
      )
    } else return (
      <Dialog>
        <span className="dialog-title">Deliver items</span>
        <span className="dialog-text">Where do you want to send these items?</span>
        <Dropdown
          source={teams}
          onChange={(val) => this.handleDestinationChange(val)}
          value={this.state.destination}
        />
        <div className="dialog-actions">
          <button className="dialog-button dialog-cancel" style={{display: this.state.loading?"none":""}} onClick={this.props.onCancel}>Cancel</button>
          <button className="dialog-button" onClick={this.handleDeliver.bind(this)}>{this.state.loading?"Delivering...":"Confirm"}</button>
        </div>
      </Dialog>
    )
  }

  handleDestinationChange(val) {
    this.setState({destination: val})
  }

}
