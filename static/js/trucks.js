// ... existing code ...
            // Process overhead expenses first
            const expensesList = document.getElementById('expenses-list');
            expensesList.innerHTML = '';

            let totalExpenses = 0;

            // Process each truck as a line item
            trucksData.trucks.forEach(truck => {
                const crewWages = truck.employees.reduce((sum, emp) => 
                    sum + (parseFloat(emp.hourly_wage) * parseFloat(emp.hours_per_week) * 4), 0);
                
                const truckExpenses = (parseFloat(truck.loan_payment) || 0) +
                    (parseFloat(truck.insurance) || 0) +
                    (parseFloat(truck.fuel_budget) || 0) +
                    (parseFloat(truck.maintenance_budget) || 0) +
                    (parseFloat(truck.other_expenses) || 0);
                
                const totalTruckMonthlyExpenses = truckExpenses + crewWages;
                totalExpenses += totalTruckMonthlyExpenses;

                // Add truck as a line item
                expensesList.innerHTML += `
                    <tr>
                        <td>${truck.name}</td>
                        <td class="text-end">${formatCurrency(totalTruckMonthlyExpenses)}</td>
                    </tr>
                `;
            });

            // Update the total expenses
            document.getElementById('expenses-total-value').textContent = formatCurrency(totalExpenses);
// ... existing code ... 