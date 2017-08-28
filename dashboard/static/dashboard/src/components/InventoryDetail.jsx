import React from 'react'
import $ from 'jquery'
import {display} from './Task.jsx'
import {fetch, post} from './APIManager.jsx'
import update from 'immutability-helper'
import {Link} from 'react-router-dom'
import Loading from './Loading.jsx'
import {Dropdown} from 'react-toolbox/lib/dropdown'
import {Dialog} from './Dialog.jsx'

class InventoryDetail extends React.Component {

  constructor(props) {
    super(props)
    this.latestRequestID = -1
    this.handleLoadClick = this.handleLoadClick.bind(this)
    this.state = { 
      tasks: [],
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

    var contentArea = <ItemList 
      {...props} 
      tasks={this.state.tasks} 
      onChange={this.handleItemSelect.bind(this)} 
      onSelectAll={this.handleSelectAllToggle.bind(this)}
    />
    var loading = false
    if (this.state.loading) {
      loading = <Loading />
    }

    let loadMore = false
    if (this.state.next && !this.state.loading) {
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
          { loading }
          { loadMore }
        </div>
        <div className="i-detail-footer">
          { deliver }
        </div>
      </div>
    )
  }

  getInventoryItems(props, u) {
    if (!props.match.params.id) {
      return
    }

    let newState = {loading: true}
    if (!u) {
      newState.tasks = []
      newState.selectedCount = 0
    }

    this.setState(newState)

    let url = u || window.location.origin + "/ics/inventory/detail-test/"// + props.match.params.id
    let g = {process: props.match.params.id}
    if(this.props.filter) {
      g.products = this.props.filter
    }

    if (props.count > 500) {
      g.page_size = 5
    }

    let random = Math.floor(Math.random() * 1000)
    this.latestRequestID = random

    let component = this
    fetch(url, g)
      .done(function (data, d, jqxhr) {
        if (component.latestRequestID == random) {
          var tasks = data.results
          if(u) {
            tasks = update(component.state.tasks, {$push: tasks})
          }
          component.setState({tasks: tasks, next: data.next, loading: false})

        }
      }).fail(function () {
        alert("error!")
        component.setState({loading: false})
      })
  }

  handleSelectAllToggle(taskIndex) {
    let task = this.state.tasks[taskIndex]
    
    // get count of selected in this task
    let count = 0
    for (var item of task.items) {
      count += (item.selected ? 1 : 0)
    }

    // make a deep copy of the array
    let newTask = update(task, {$merge: []})
    let totalSelected = this.state.selectedCount

    if (count == 0) {
      for (var i = 0; i < newTask.items.length; i++) {
        newTask.items[i].selected = true
        totalSelected += 1
      }
    } else {
      for (var i = 0; i < newTask.items.length; i++) {
        if (newTask.items[i].selected) {
          newTask.items[i].selected = false
          totalSelected -= 1
        }
      }
    }

    this.setState({task: newTask, selectedCount: totalSelected})

  }

  updateItem(itemArray, index, merge) {
    return update(itemArray, index)
  }

  handleItemSelect(taskIndex, itemIndex) {

    // get the toggled selection value
    let newVal = !(this.state.tasks[taskIndex].items[itemIndex].selected)

    // get the count of selected items 
    // after toggling this item's selection value
    let newCount = this.state.selectedCount
    if (newVal) {
      newCount =this.state.selectedCount + 1
    } else {
      newCount = this.state.selectedCount - 1
    }

    // update the task object
    let newArr = update(this.state.tasks, {
      [taskIndex]: {
        items: {
          [itemIndex]: {
            $merge: {selected: newVal}
          }
        }
      }
    })

    // update the state with new task object & selected count
    this.setState({tasks: newArr, selectedCount: newCount})
  }

  deliverItems(destination, callback) {
    let tasks = this.state.tasks

    let itemsToDeliver = []
    for (let task of this.state.tasks) {
      for (let item of task.items) {
        if (item.selected) {
          itemsToDeliver.push({item: `${item.id}`})
        }
      }
    }

    console.log(itemsToDeliver)

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

    let headers = {
      contentType: 'application/json',
      processData: false,
    }

    post(url, JSON.stringify(params), headers)
      .done(function (data) {
        if (callback) 
          callback()
        component.props.onDelivery(component.state.selectedCount)
        //component.getInventoryItems(component.props, null)
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
      (props.tasks || []).map(function (task, i) {
        return <TaskDropdown key={i} index={i} {...task} onChange={props.onChange} onSelectAll={props.onSelectAll}/>
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
          <span className="item-qr">{props.item_qr.substring(43)}</span>
        </div>
      </div>
      <div className="unflex">
        <input 
          type="checkbox" 
          value={props.selected} 
          checked={props.selected} 
          onChange={() => props.onChange(props.taskIndex, props.itemIndex)}
        />
      </div>
    </div>
  )
}

function TaskDropdown(props) {

  return (
    <div className="inventory-task">
      <div className="task-title">
        <a 
          href={window.location.origin + "/dashboard/task/" + props.id}
          target="_blank"
        >
          <span className="item-task">{` ${props.display} (${props.items.length})`}</span>
        </a>
        <button onClick={() => props.onSelectAll(props.index)}>all/none</button>
      </div>
    {
      props.items.map(function (item, i) {
        return <Item {...item} key={i} itemIndex={i} taskIndex={props.index} onChange={props.onChange} />
      })
    }
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

export {InventoryDetail, DeliveryDialog}
