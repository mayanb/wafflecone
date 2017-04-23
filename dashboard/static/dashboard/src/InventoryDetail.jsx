import React from 'react'
import $ from 'jquery'
import {display} from './Task.jsx'
import {fetch} from './APIManager.jsx'
import update from 'immutability-helper'
import {Link} from 'react-router-dom'
import Loading from './Loading.jsx'

export default class InventoryDetail extends React.Component {

  constructor(props) {
    super(props)
    this.latestRequestID = -1
    this.handleLoadClick = this.handleLoadClick.bind(this)
    this.state = { 
      items: [],
      next: null,
      loading: false,
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

    var contentArea = <ItemList {...props} items={this.state.items}/>
    if (!this.state.items || this.state.items.length == 0) {
      if (this.state.loading) {
        contentArea = <Loading />
      }
    }

    let loadMore = false
    if (this.state.next) {
      loadMore = <button onClick={this.handleLoadClick}>Load More</button>
    }

    return (
      <div className={"inventory-detail " + (props.showDetail?"":"smallDetail")}>
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
          if(u) {
            items = update(component.state.items, {$push: items})
          }
          component.setState({items: items, next: data.next})
        }
      }).always(function () {
        component.setState({loading: false})
      })
  }
}

function ItemList(props) {
  return (
    <div>
    {
      (props.items || []).map(function (item, i) {
        return <Item key={i} {...item}/>
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
        <input type="checkbox" onChange={null} />
      </div>
    </div>
  )
}