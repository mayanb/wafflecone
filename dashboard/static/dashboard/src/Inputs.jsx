import React from 'react';
import ReactDOM from 'react-dom';
import Select from 'react-select';
import Datepicker from './Datepicker.jsx'
import WrapMenu from './WrapMenu.jsx'
import $ from 'jquery';
import {display} from './Task.jsx'

var getOptions = function(input, callback) {
    if (input.length < 2) {
      callback(null, { optionss: [] })
    } else {
      $.get(window.location.origin + "/ics/tasks/?limit&ordering=-created_at&label=" + input).done(function (data) {
        var options = data.map(function (x) {
          return { value: x.id, label: display(x)}
        })
        callback(null, {options : options, complete: false})
      })
    }
  }

class TaskSelect extends React.Component {
  constructor() {
    super();
    this.handleChange = this.handleChange.bind(this);
    this.state = {}

  }

  handleChange(value) {
    var v;
    if (value != undefined && value != null && value.length != 0)
      v = value
    else v = {value: ""}

    this.setState(v)
    this.props.onChange(v)
  };

  render () {
    return (
      <div className="multiselect">
        <Select.Async
          name="form-field-name"
          value={this.state.value}
          loadOptions={getOptions}
          onChange={this.handleChange}
          placeholder={this.props.placeholder}
        />
      </div>
    );
  }


}

class Multiselect extends React.Component {

 constructor() {
    super();
    this.handleMultipleChange = this.handleMultipleChange.bind(this);
    this.state = {
      value: [],
    };
  }

  handleMultipleChange(value) {
    this.props.onChange(value)
    this.setState({value: value});
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.value != this.state.value) {
      this.setState({value: nextProps.value })
    }
  }

  render () {
    return (
      <div className="multiselect">
        <Select multi
          name="form-field-name"
          value={this.state.value}
          options={this.getSelect(this.props.options)}
          onChange={this.handleMultipleChange}
          placeholder={this.props.placeholder}
          clearable={false}
        />
      </div>
    );
  }

  getSelect(options) {
    if (!options)
      return;

    return Object.keys(options).map(function (key, i) {
      return {value: options[key].id, label: options[key].name}
    })

  }

}

class Filters extends React.Component {

  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.handleProcessChange = this.handleProcessChange.bind(this);
    this.handleProductChange = this.handleProductChange.bind(this);
    this.handleDateRangeChange = this.handleDateRangeChange.bind(this);
    this.handleParentChange = this.handleParentChange.bind(this);
    this.handleChildChange = this.handleChildChange.bind(this);
    this.state = {
      processes: [],
      products: [],
      parent: "",
      start: "",
      end: "",
      active: 1
    }
  }

  handleFilter() {
    var filters = {}

    if (this.state.active == 1) {
      filters.processes = this.state.processes
      filters.products = this.state.products
      filters.start = this.state.start
      filters.end = this.state.end
    } else if (this.state.active == 2) {
      filters.parent = this.state.parent
    } else if (this.state.active == 3) {
      filters.child = this.state.child
    }

    this.props.onFilter(filters)

  }

  componentWillReceiveProps(nextProps) {
    if (this.props.dates != nextProps.dates) {
      this.setState( {
      processes: [],
      products: [],
      parent: "",
      start: "",
      end: "",
      active: 1})
    }
  }

  handleChange(which, payload) {
    this.props.onFilter({[which] : payload })
  }

  handleDateRangeChange(date) {
    this.props.onFilter(date)
  }

  switchActive(x) {
    this.props.onFilter({active : x})
  }

  handleProcessChange(val) {
    console.log("processes")
    this.setState({processes: val}, this.handleFilter)
  }

  handleProductChange(val) {
    console.log("products")
    this.setState({products: val}, this.handleFilter)
  }


  handleParentChange(val) {
    console.log("parent")
    this.setState({parent: val.value}, this.handleFilter)
  }

  handleChildChange(val) {
    this.setState({child: val.value}, this.handleFilter)
  }

  render () {

    var obj = false

    if (this.props.dates) {
      obj = <div style={{marginLeft: "8px", flex: "1 auto"}}><Datepicker onChange={(val) => this.handleDateRangeChange(val)} /></div>
    }

    return (
      <div className="filters inputs">

            <div className="active section">
              
              <div className="section-content">

                <div>
                  <TaskSelect placeholder="All tasks" onChange={(val) => this.handleChange("parent", val)} />
                </div>

                <div style={{display: "flex", flexdirection: "row"}}>
                  <div style={{marginRight: "8px", flex: "1 auto"}}>
                    <Multiselect options={this.props.processes} value={this.props.filters.processes} placeholder="All processes" onChange={(val) => this.handleChange("processes", val)}/>
                  </div>

                  <div style={{flex: "1 auto"}}>
                    <Multiselect options={this.props.products} value={this.props.filters.products} valueArray={this.props.filters.products} placeholder="All products" onChange={(val) => this.handleChange("products", val)}/>
                  </div>

                  {obj}

                </div>


              </div>
            </div>
        </div>
    );
  }
}

export { Filters };