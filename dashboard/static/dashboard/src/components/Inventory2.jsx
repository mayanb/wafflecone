import React from 'react'
import $ from 'jquery'
import {Link} from 'react-router-dom'
import InventoryDetail from './InventoryDetail.jsx'
import { InventoryFilter, Filters } from './Inputs.jsx'
import {fetch, requestID, ZeroState} from './APIManager.jsx'
import Loading from './Loading.jsx'
import update from 'immutability-helper'

export default class Inventory extends React.Component {
  constructor(props) {
    super(props)
    this.handleProductFilter = this.handleProductFilter.bind(this)
    this.latestRequestID = -1
    this.state = {
      processes: [],
      products: [],
      loading: false,
      selected: -1,
      productFilter: [],
      productFilterStr: ""
    }
  }

  getProcessesForInventory() {
    this.setState({loading: true})

    let url = window.location.origin + "/ics/inventory/"

    var params = {}
    if (this.state.productFilter.length > 0)
      params={products:this.state.productFilterStr}

    console.log(params)

    let component = this
    let rid = requestID()
    this.latestRequestID = rid

    fetch(url, params)
      .done(function (data) {
        if (component.latestRequestID == rid)
          component.setState({processes : data})
      })
      .always(function () {
        if (component.latestRequestID == rid)
          component.setState({loading: false})
      })
  }

  getProductsForInventory() {
    let component = this
    let url = window.location.origin + "/ics/products/codes/"
    $.get(url)
      .done(function (data) {
        let mappedProducts = data.map(function (product, i) {
          return {value: product.id, label: product.name}
        })
        component.setState({products: data})
      })
  }

  componentDidMount() {
    this.getProcessesForInventory()
    this.getProductsForInventory()
  }

  handleProductFilter(which, val) {
    let component = this
    let valStr = val.map(function (v, i) {
      return v.code
    }).join()
    this.setState({[which] : val, productFilterStr : valStr}, function () {
      component.getProcessesForInventory()
    })
  }

  getSelectedProcess() {
    let a = this.state.processes.find(function (x) {
      return (x.process_id == this.props.match.params.id)
    }, this)
    return a
  }

  handleDelivery(selectedCount) {
    var processIndex = 0
    for (let [index, process] of this.state.processes.entries()) {
      if (process.process_id == this.props.match.params.id) {
        processIndex = index
        break
      }
    }

    let newProcesses = update(this.state.processes, {
      [processIndex]: {
        count: {
          $apply: function (c) { return c - selectedCount }
        }
      }
    })

    this.setState({processes: newProcesses})

  }

  render() {
    let props = this.props

    var contentArea = <InventoryList processes={this.state.processes} selected={props.match.params.id} />
    if (this.state.loading) {
      contentArea = <Loading />
    } else if (!this.state.processes || this.state.processes.length == 0) {
      contentArea = <ZeroState filtered={this.state.productFilter && this.state.productFilter.length} />
    }

    return (
      <div className="inventory">
        <div className={"page inventory-list " + (props.match.params.id?"smallDetail":"")}>
          <div className="inventory-header page-header">
            <h2>Inventory</h2>
            <InventoryFilter options={this.state.products} onFilter={this.handleProductFilter} selected={this.state.productFilter} />
          </div>
          {contentArea}
        </div>
        <InventoryDetail 
          {...this.getSelectedProcess()} 
          filter={this.state.productFilter.length>0?this.state.productFilterStr:null} 
          match={props.match} 
          showDetail={props.match.params.id}
          onDelivery={this.handleDelivery.bind(this)}
        />
      </div>
    )
  }
}

function InventoryList(props) {
  return (
    <div>
      <InventoryItem i={"no"} header={true} output_desc={"PRODUCT TYPE"} count={"COUNT"} unit={"UNIT"} oldest={"OLDEST"} />
      {
        props.processes.map(function (process, i) {
          return  (
            <Link key={i} to={ "/dashboard/inventory/" + process.process_id}>
              <InventoryItem i={i} selected={props.selected} {...process}/>
            </Link>
          )
        }, this)
      }
    </div>
  )
}


function InventoryItem(props) {
  var teamStyle = {color: "rgba(0,0,0,0.3", paddingLeft: "4px", fontSize: "10px"}
  let currTeam = window.localStorage.getItem("team") || "1"
  teamStyle["display"] = currTeam==props.team_id?"none":""
  return (
    <div className={"inventoryClass " + isSelected(props) + " " + isHeader(props)} onClick={props.onClick}>
      <div className="i-outputdesc">
        <span>{props.output_desc.sentenceCase()}</span>
        <span style={teamStyle}>{props.team}</span>
      </div>
      <div className="i-count">
        <span>{props.count}</span>
      </div>
      <div className="i-unit">
        <span>{props.unit.sentenceCase() + "s"}</span>
      </div>
      <div className="i-date">
        <span>{props.date}</span>
      </div>
    </div>
  )
}

function isHeader(props) {
  return (props.header == true) ? "inventoryClass-header" : ""
}

function isSelected(props) {
  if (isHeader(props))
    return false
  return (props.process_id == props.selected) ? "selected" : ""
}

String.prototype.sentenceCase = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}