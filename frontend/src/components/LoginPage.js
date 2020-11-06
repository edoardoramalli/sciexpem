import React from "react";

import BasicPage from "./BasicPage";
import LoginForm from "./LoginForm";

class  LoginPage extends React.Component{
    render() {
        return(
            <BasicPage element={<LoginForm />} />
        )
    }
}

export default LoginPage;