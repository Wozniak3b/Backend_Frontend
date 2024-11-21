import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function ProtectedPage() {
    const navigate = useNavigate();
    const [totalDebt, setTotalDebt] = useState('');
    const [debts, setDebts] = useState([]);
    const [name, setName] = useState('');
    const [allUsers, setUsers] = useState([]);
    const [userId, setUserId] = useState('');
    const [title, setTitle] = useState('');
    const [debtValue, setDebtValue] = useState('');

    //HAVE TO CHANGE ERROR HANDLING!!!

    useEffect(() => {
        const verifyToken = async () => {
            //What out token is
            const token = localStorage.getItem('token');
            //For us only, dont use in code
            //console.log(token)
            if (!token) {
                console.error('No token found');
                navigate('/login');
                return;
            }

            const username = localStorage.getItem('username');
            setName(username);

            try {

                //Token path to verify token
                const response = await fetch(`http://localhost:8000/verify-token`, {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Token verification has failed!');
                }

                //--------------------------------------------------------------------------------

                const sumResponse = await fetch(`http://localhost:8000/protected/debts/sum/`, {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });

                if (!sumResponse.ok) {
                    throw new Error("Failed to fetch debts summary!");
                }

                const sumData = await sumResponse.json();
                setTotalDebt(sumData.totalDebt);

                //--------------------------------------------------------------------------------

                const debtsResponse = await fetch(`http://localhost:8000/protected/debts/all/`, {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });

                if (!debtsResponse.ok) {
                    throw new Error("Failed to fetch debts!");
                }

                const debtsData = await debtsResponse.json();
                setDebts(debtsData.all_user_debts);

                //--------------------------------------------------------------------------------

            } catch (error) {
                console.error("Error fetching data:", error);
                localStorage.removeItem('token');
                //navigate('/login');
            }
        };
        verifyToken();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
        window.location.reload();
    };

    const deleteDebt = async (debtId) => {
        const token = localStorage.getItem('token');
        try {
            const deleteResponse = await fetch(`http://localhost:8000/protected/debts/${debtId}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!deleteResponse.ok) {
                throw new Error("Failed to delete debt!");
            }

            setDebts(debts.filter(debt => debt.id !== debtId));
            alert("Debt paid succesfully!")
            window.location.reload();
        } catch (error) {
            console.log("Error deleteing debt:", error)
        }
    };

    const getUsers = async () => {
        const token = localStorage.getItem('token');
        try {
            const usersResponse = await fetch(`http://localhost:8000/protected/users`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!usersResponse.ok) {
                throw new Error("Failed to get all users!");
            }

            const usersData = await usersResponse.json();
            setUsers(usersData.allUsers)

        } catch (error) {
            console.log("Error getting users:", error)
        }
    };

    useEffect(() => {
        getUsers();
    }, []);

    //We can do this by using local function e, idk if its better
    const handleSelect = (event) => {
        const selectedUserId = event.target.value;
        const selectedUser = allUsers.find(user => user.id === parseInt(selectedUserId));
        if (selectedUser) {
            setUserId(selectedUserId);
        }
    };

    const createDebt = async (event) => {
        const token = localStorage.getItem('token');
        event.preventDefault();
        const receiver = name;
        const amount = debtValue;
        const user_id = userId

        const formDetails = {
            title,
            receiver,
            amount,
            user_id
        }

        try {
            const response = await fetch("http://localhost:8000/protected/debts/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formDetails)
            });

            if (response.ok) {
                alert("Debt added succesfully!");
            }
            else {
                throw new Error("Failed to add debt!");
            }
        } catch (error) {
            console.error("Error while adding debt", error)
        }
    };


    return (
        <main>
            <h2>Welcome {name}</h2>
            <h3>Your debt is: {totalDebt} zł</h3>
            <section>
                <h4>Your debts:</h4>
                {debts.length === 0 ? (
                    <p>You have no debts.</p>  // If no debts, show a message
                ) : (
                    <ul>
                        {debts.map((debt) => (
                            <li key={debt.id}>
                                <strong>{debt.title}</strong> to {debt.receiver} — {debt.amount} zł
                                <button onClick={() => deleteDebt(debt.id)}>Paid</button>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
            <form onSubmit={createDebt}>
                <h4>Add new receipt here</h4>
                <label htmlFor="title">Title:</label>
                <input type="text" name="title" placeholder="Title"
                    onChange={(e) => setTitle(e.target.value)}></input>
                <label htmlFor="value">Value:</label>
                <input type="number" name="value" min="0" step="0.01"
                    onChange={(e) => setDebtValue(e.target.value)}></input>
                <label htmlFor="receiver">To:</label>
                <select name="receiver" onChange={handleSelect} value={userId}>
                    <option value="">Choose receiver</option>
                    {allUsers.map((user) => (
                        <option key={user.id} value={user.id} id={user.username}>
                            {user.username}
                        </option>
                    ))}
                </select>
                <button type="submit">Add debt</button>
            </form>
            <button onClick={handleLogout}>Logout</button>
        </main >
    )
}

export default ProtectedPage;