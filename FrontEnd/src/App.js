import React, { Component } from "react";
import { render } from "react-dom";
import { Router, Route, Link } from 'react-router';
import { DatePicker } from 'antd';
import BasicPage from "./components/BasicPage";
import NavBar from "./components/NavBar";
import LoginPage from "./components/LoginPage";


class App extends Component {

    render() {
        return (
            <div>
                <LoginPage />
            </div>

        );
    }
}

export default App;
