import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.models.digital_twin import (
    DigitalTwinBaseline,
    OperationalParameters,
    SimulationLevers,
    ProjectedMetrics,
    DeltaComparison,
    MonthlyProjectionPoint,
    AIInsights,
    ScenarioPreset,
)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SEASONAL_WEIGHTS = [1.05, 0.95, 0.90, 0.92, 0.98, 1.02, 1.08, 1.15, 1.30, 1.45, 1.25, 1.10]


class DigitalTwinAIEngine:
    """
    Pure sandbox predictive simulation engine for artisan digital twins.
    Simulates business outcomes before real decisions are executed.
    """

    @staticmethod
    def get_standard_presets() -> List[ScenarioPreset]:
        return [
            ScenarioPreset(
                id="preset_price_plus_10",
                name="Increase Price by 10%",
                description="Test market elasticity and gross profit margin expansion without altering production capacity.",
                icon="TrendingUp",
                scenario_type="price_change",
                default_levers=SimulationLevers(
                    price_adjustment_pct=10.0,
                    simulation_horizon_months=6,
                )
            ),
            ScenarioPreset(
                id="preset_festival_discount",
                name="Launch Festival Discount (20%)",
                description="Simulate Diwali / festive sales spike with high volume velocity and seasonal demand multipliers.",
                icon="Sparkles",
                scenario_type="festival_discount",
                default_levers=SimulationLevers(
                    festival_discount_pct=20.0,
                    marketing_boost_pct=25.0,
                    simulation_horizon_months=6,
                )
            ),
            ScenarioPreset(
                id="preset_produce_100_extra",
                name="Produce 100 Extra Units",
                description="Evaluate inventory carrying cost, stockout reduction, and working capital cash lockup.",
                icon="Package",
                scenario_type="produce_extra",
                default_levers=SimulationLevers(
                    extra_units_produced=100,
                    simulation_horizon_months=6,
                )
            ),
            ScenarioPreset(
                id="preset_hire_one_worker",
                name="Hire 1 Additional Master Artisan",
                description="Increase monthly production capacity by 40 units while accounting for wage overhead and reduced lead times.",
                icon="Users",
                scenario_type="hire_worker",
                default_levers=SimulationLevers(
                    hire_workers_count=1,
                    simulation_horizon_months=6,
                )
            ),
            ScenarioPreset(
                id="preset_open_export",
                name="Open Global Export Sales",
                description="Unlock international cross-border buyers in MENA, US, and EU with 35% premium export pricing.",
                icon="Globe",
                scenario_type="open_export",
                default_levers=SimulationLevers(
                    enable_export=True,
                    shipping_region="Global (Export)",
                    simulation_horizon_months=6,
                )
            ),
            ScenarioPreset(
                id="preset_change_shipping_region",
                name="Expand to Pan-India Express Delivery",
                description="Simulate expanding fulfillment zones to Tier-1 and Tier-2 clusters across all Indian postal zones.",
                icon="Truck",
                scenario_type="change_shipping_region",
                default_levers=SimulationLevers(
                    shipping_region="Pan-India",
                    marketing_boost_pct=15.0,
                    simulation_horizon_months=6,
                )
            )
        ]

    def simulate(
        self,
        baseline: DigitalTwinBaseline,
        params: OperationalParameters,
        levers: SimulationLevers
    ) -> Tuple[ProjectedMetrics, DeltaComparison, List[MonthlyProjectionPoint], AIInsights]:
        """
        Calculates deterministic and probabilistic business projections based on applied scenario levers.
        """
        base_price = baseline.unit_price_avg
        base_cost = baseline.unit_cost_avg
        base_orders = baseline.monthly_orders
        base_workers = baseline.worker_count
        base_capacity = baseline.production_capacity_monthly
        base_inventory = baseline.inventory_units
        base_customers = baseline.active_customers
        base_monthly_revenue = baseline.revenue_monthly

        # 1. Effective Price Calculation
        effective_price = base_price * (1.0 + (levers.price_adjustment_pct / 100.0))
        if levers.festival_discount_pct > 0:
            effective_price *= (1.0 - (levers.festival_discount_pct / 100.0))
        if levers.enable_export:
            effective_price *= (1.0 + (params.export_markup_pct / 100.0))

        # 2. Demand Elasticity & Multipliers
        price_change_ratio = (effective_price - base_price) / max(base_price, 1.0)
        # Standard economic elasticity: % change in Q = Elasticity * % change in P
        elasticity_factor = 1.0 + (params.price_elasticity * price_change_ratio)
        elasticity_factor = max(0.35, min(2.5, elasticity_factor))

        festival_multiplier = 1.0
        if levers.festival_discount_pct > 0:
            # Festival discount creates volume elasticity surge + festive demand
            festival_multiplier = 1.0 + (levers.festival_discount_pct * 0.022) * params.seasonal_index

        export_multiplier = 1.35 if levers.enable_export else 1.0
        marketing_multiplier = 1.0 + (levers.marketing_boost_pct * 0.008)

        region_multiplier = 1.0
        if levers.shipping_region == "Tier-1 Metro Only":
            region_multiplier = 0.88  # Narrower addressable market, higher basket
        elif levers.shipping_region == "Global (Export)":
            region_multiplier = 1.25
        elif levers.shipping_region == "Pan-India":
            region_multiplier = 1.12

        projected_monthly_demand = int(round(
            base_orders * elasticity_factor * festival_multiplier * export_multiplier * marketing_multiplier * region_multiplier
        ))
        projected_monthly_demand = max(5, projected_monthly_demand)

        # 3. Production Capacity & Worker Output
        sim_workers = base_workers + levers.hire_workers_count
        sim_production_capacity = sim_workers * params.worker_capacity_units + levers.extra_units_produced
        
        # 4. Inventory, Units Sold & Stockout Probability
        available_stock = base_inventory + sim_production_capacity
        units_sold = min(projected_monthly_demand, available_stock)
        inventory_end = max(0, available_stock - units_sold)
        
        stockout_risk_pct = 0.0
        if projected_monthly_demand > available_stock:
            unfulfilled = projected_monthly_demand - available_stock
            stockout_risk_pct = round(min(95.0, (unfulfilled / projected_monthly_demand) * 100.0), 1)
        elif inventory_end < (projected_monthly_demand * 0.25):
            stockout_risk_pct = round(max(5.0, 35.0 - (inventory_end / max(projected_monthly_demand, 1)) * 30.0), 1)
        else:
            stockout_risk_pct = 4.5

        # 5. Financial Modeling: Revenue, Costs & Profit
        sim_revenue = round(units_sold * effective_price, 2)
        
        # Variable production cost + export packaging
        unit_variable_cost = base_cost
        if levers.enable_export:
            unit_variable_cost += 150.0  # International export packaging & documentation
        
        variable_costs = units_sold * unit_variable_cost
        worker_wages = sim_workers * params.worker_monthly_wage
        fixed_overhead = params.fixed_monthly_overhead + (levers.marketing_boost_pct * 120.0)
        
        total_costs = variable_costs + worker_wages + fixed_overhead
        sim_profit = round(sim_revenue - total_costs, 2)
        sim_margin_pct = round((sim_profit / max(sim_revenue, 1.0)) * 100.0, 1)

        # 6. Workload & Capacity Utilization
        capacity_utilization_pct = round(min(100.0, (units_sold / max(sim_production_capacity, 1)) * 100.0), 1)
        # Standard artisan workshop lead hours per unit
        hours_per_unit = 3.5
        delivery_workload_hours = round(units_sold * hours_per_unit / max(sim_workers, 1), 1)

        # 7. Customer Growth & Acquisition
        customer_growth_rate = 0.05
        if levers.festival_discount_pct > 0:
            customer_growth_rate += (levers.festival_discount_pct * 0.006)
        if levers.enable_export:
            customer_growth_rate += 0.18
        if levers.marketing_boost_pct > 0:
            customer_growth_rate += (levers.marketing_boost_pct * 0.004)
        if levers.price_adjustment_pct > 15:
            customer_growth_rate -= 0.04
        
        customer_growth_pct = round(customer_growth_rate * 100.0, 1)
        sim_active_customers = int(round(base_customers * (1.0 + customer_growth_rate)))

        # 8. Projected Monthly Time Series (Horizon)
        horizon = levers.simulation_horizon_months
        current_month_idx = datetime.now().month - 1
        monthly_projections: List[MonthlyProjectionPoint] = []

        curr_sim_inv = base_inventory
        curr_base_inv = base_inventory
        curr_sim_cust = base_customers
        curr_base_cust = base_customers

        for m in range(1, horizon + 1):
            m_idx = (current_month_idx + m - 1) % 12
            month_name = MONTH_NAMES[m_idx]
            season_mult = SEASONAL_WEIGHTS[m_idx]

            # Baseline month
            m_base_demand = int(round(base_orders * season_mult))
            m_base_sold = min(m_base_demand, curr_base_inv + base_capacity)
            curr_base_inv = max(0, curr_base_inv + base_capacity - m_base_sold)
            m_base_rev = round(m_base_sold * base_price, 2)
            m_base_profit = round(m_base_rev * (baseline.profit_margin_pct / 100.0), 2)
            curr_base_cust = int(round(curr_base_cust * 1.02))

            # Simulated month
            m_sim_demand = int(round(projected_monthly_demand * season_mult))
            m_monthly_capacity = sim_workers * params.worker_capacity_units
            if m == 1:
                m_monthly_capacity += levers.extra_units_produced
            
            m_sim_sold = min(m_sim_demand, curr_sim_inv + m_monthly_capacity)
            curr_sim_inv = max(0, curr_sim_inv + m_monthly_capacity - m_sim_sold)
            m_sim_rev = round(m_sim_sold * effective_price, 2)
            m_sim_profit = round(m_sim_rev - (m_sim_sold * unit_variable_cost + worker_wages + fixed_overhead), 2)
            curr_sim_cust = int(round(curr_sim_cust * (1.0 + (customer_growth_rate / max(horizon, 1)))))

            monthly_projections.append(MonthlyProjectionPoint(
                month=m,
                month_name=month_name,
                baseline_revenue=m_base_rev,
                simulated_revenue=m_sim_rev,
                baseline_profit=m_base_profit,
                simulated_profit=m_sim_profit,
                baseline_demand=m_base_demand,
                simulated_demand=m_sim_demand,
                baseline_inventory=curr_base_inv,
                simulated_inventory=curr_sim_inv,
                baseline_workload_hours=round(m_base_sold * hours_per_unit / max(base_workers, 1), 1),
                simulated_workload_hours=round(m_sim_sold * hours_per_unit / max(sim_workers, 1), 1),
                baseline_customers=curr_base_cust,
                simulated_customers=curr_sim_cust,
            ))

        # 9. Delta Comparison
        rev_delta = round(sim_revenue - base_monthly_revenue, 2)
        rev_delta_pct = round((rev_delta / max(base_monthly_revenue, 1.0)) * 100.0, 1)
        
        base_profit = round(base_monthly_revenue * (baseline.profit_margin_pct / 100.0), 2)
        profit_delta = round(sim_profit - base_profit, 2)
        profit_delta_pct = round((profit_delta / max(abs(base_profit), 1.0)) * 100.0, 1)

        demand_delta = projected_monthly_demand - base_orders
        demand_delta_pct = round((demand_delta / max(base_orders, 1)) * 100.0, 1)
        inv_delta = inventory_end - base_inventory
        workload_delta = round(delivery_workload_hours - (base_orders * hours_per_unit / max(base_workers, 1)), 1)
        cust_delta = sim_active_customers - base_customers

        deltas = DeltaComparison(
            revenue_delta=rev_delta,
            revenue_delta_pct=rev_delta_pct,
            profit_delta=profit_delta,
            profit_delta_pct=profit_delta_pct,
            demand_delta_units=demand_delta,
            demand_delta_pct=demand_delta_pct,
            inventory_delta_units=inv_delta,
            workload_delta_hours=workload_delta,
            customer_growth_delta=cust_delta,
        )

        projected = ProjectedMetrics(
            revenue_monthly=sim_revenue,
            profit_monthly=sim_profit,
            profit_margin_pct=sim_margin_pct,
            demand_units_monthly=projected_monthly_demand,
            units_sold_monthly=units_sold,
            inventory_end_units=inventory_end,
            stockout_risk_pct=stockout_risk_pct,
            delivery_workload_hours=delivery_workload_hours,
            capacity_utilization_pct=capacity_utilization_pct,
            customer_growth_pct=customer_growth_pct,
            active_customers=sim_active_customers,
        )

        # 10. AI Insights & Strategic Synthesis
        opportunities: List[str] = []
        warnings: List[str] = []
        actions: List[str] = []

        if rev_delta > 0 and profit_delta > 0:
            opportunities.append(f"Projected net monthly profit increases by ₹{profit_delta:,.0f} (+{profit_delta_pct}%) with strong economic viability.")
        if levers.enable_export:
            opportunities.append(f"Global export expansion captures premium foreign margins (+{params.export_markup_pct}% unit value) with international brand footprint.")
        if levers.festival_discount_pct > 0:
            opportunities.append(f"Festive promotion creates a {demand_delta_pct}% volume lift and accelerates new customer acquisition by +{customer_growth_pct}%.")
        if levers.hire_workers_count > 0:
            opportunities.append(f"Adding {levers.hire_workers_count} master artisan(s) expands production buffer by +{levers.hire_workers_count * params.worker_capacity_units} units/month.")

        if stockout_risk_pct > 25.0:
            warnings.append(f"High stockout risk ({stockout_risk_pct}%): Projected monthly demand of {projected_monthly_demand} units exceeds available supply.")
        if sim_profit < base_profit and rev_delta > 0:
            warnings.append("Margin dilution alert: Higher sales volume is offset by increased labor or marketing expenditures.")
        if capacity_utilization_pct > 92.0 and levers.hire_workers_count == 0:
            warnings.append(f"Workshop bottleneck risk: {capacity_utilization_pct}% capacity utilization leaves zero margin for order surges or equipment downtime.")

        if stockout_risk_pct > 20.0:
            actions.append(f"Pre-order raw craft materials immediately and increase production batch size by {projected_monthly_demand - available_stock} units.")
        if levers.price_adjustment_pct > 0 and demand_delta_pct > -10.0:
            actions.append("Price inelasticity confirmed: The marketplace readily accepts the +10% price revision without severe volume drop.")
        if not levers.enable_export and baseline.export_active is False:
            actions.append("Consider piloting GCC & EU export shipping with automated currency conversion to capture higher dollar margins.")
        if not actions:
            actions.append("Maintain current operational equilibrium while monitoring supplier raw material lead times.")

        summary = (
            f"The digital twin sandbox indicates that executing this scenario will result in a projected monthly revenue "
            f"of ₹{sim_revenue:,.0f} ({'+' if rev_delta >= 0 else ''}{rev_delta_pct}%) and net profit of ₹{sim_profit:,.0f} "
            f"({'+' if profit_delta >= 0 else ''}{profit_delta_pct}%), while serving {sim_active_customers} active customers."
        )

        insights = AIInsights(
            summary=summary,
            key_opportunities=opportunities or ["Stable baseline cashflow maintained."],
            risk_warnings=warnings or ["No critical risk anomalies detected under this scenario."],
            recommended_actions=actions,
            confidence_score=93.5,
        )

        return projected, deltas, monthly_projections, insights


digital_twin_ai_engine = DigitalTwinAIEngine()
