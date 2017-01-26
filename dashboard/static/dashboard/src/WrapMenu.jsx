import React from 'react';
import {Menu} from 'react-toolbox/lib/menu'
import {Button} from 'react-toolbox/lib/button'

export default class WrapMenu extends React.Component {
  constructor() {
    super()
    this.handleButtonClick = this.handleButtonClick.bind(this);
    this.handleMenuHide = this.handleMenuHide.bind(this);
    this.state = { active: false };
  }

  handleButtonClick() {
    this.setState({ active: !this.state.active });
  }

  handleMenuHide() {
    this.setState({ active: false });
  }

  render () {
    return (
      <div style={{ display: 'inline-block', position: 'relative' }}>
        <Button primary raised onClick={this.handleButtonClick} label="Hello" />
        <Menu active={this.state.active} onHide={this.handleMenuHide}>
          {this.props.children}
        </Menu>
      </div>
    );
  }

}