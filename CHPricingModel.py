import pandas as pd
import matplotlib.pyplot as plt

# 1) Load CSV
csv_path = "CHPlantsFullList.csv"
df = pd.read_csv(csv_path)

df["Output_MW"] = pd.to_numeric(df["Output_MW"], errors="coerce")

# Clean fuel
df["CleanSource"] = (
    df["Source"].astype(str).str.split(";").str[0].str.strip().str.lower()
)

# Clean method (NEEDED!)
df["Method_clean"] = (
    df["Method"].astype(str).str.split(";").str[0].str.strip().str.lower()
)

# Hydro classifier
def classify_hydro(row):
    if row["CleanSource"] != "hydro":
        return None
    m = row["Method_clean"]
    if "run-of-the-river" in m:
        return "run_of_river"
    if "water-storage" in m:
        return "reservoir"
    if "water-pumped-storage" in m:
        return "pumped_storage"
    return "unknown_hydro"

df["Hydro_Type"] = df.apply(classify_hydro, axis=1)

# Marginal cost tables
hydro_costs = {
    "run_of_river": 10,
    "reservoir": 35,
    "pumped_storage": 45,
    "unknown_hydro": 25,
}

marginal_costs = {
    "solar": 0,
    "wind": 0,
    "nuclear": 30,
    "waste": 25,
    "biomass": 50,
    "biogas": 70,
    "geothermal": 60,
    "gas": 90,
    "combustion": 150,
}

# Final cost selector
def marginal_cost(row):
    source = row["CleanSource"]
    if source == "hydro":
        return hydro_costs[row["Hydro_Type"]]
    return marginal_costs.get(source, 50)

df["MarginalCost"] = df.apply(marginal_cost, axis=1)

# ---- BUILD MERIT ORDER AT PLANT LEVEL ----
# Define a block name (fuel bucket) used for stacking + labels
def block_name(row):
    if row["CleanSource"] == "hydro":
        return row["Hydro_Type"]   # e.g. run_of_river, reservoir, pumped_storage
    return row["CleanSource"]

df["Block"] = df.apply(block_name, axis=1)

# Aggregate by block: total capacity and its marginal cost
agg = (
    df.groupby("Block", dropna=False)
      .agg(
          Output_MW=("Output_MW", "sum"),
          MarginalCost=("MarginalCost", "first")
      )
      .reset_index()
      .rename(columns={"Block": "Source"})
)

# 🔧 1) Drop real NaNs
agg = agg[agg["Source"].notna()]

# 🔧 2) Drop string "nan" and "battery" buckets
agg = agg[~agg["Source"].isin(["nan", "battery"])]

# Optional: prettier hydro labels
agg["Source"] = agg["Source"].replace({
    "run_of_river": "run-of-river hydro",
    "reservoir": "reservoir hydro",
    "pumped_storage": "pumped-storage hydro",
    "unknown_hydro": "hydro (unspecified)",
})
# Sort merit order and compute cumulative capacity
agg = agg.sort_values("MarginalCost")
agg["CumCapacity"] = agg["Output_MW"].cumsum()
# Plot
plt.figure(figsize=(14, 7))
plt.step(agg["CumCapacity"], agg["MarginalCost"], where="post", linewidth=3)
plt.scatter(agg["CumCapacity"], agg["MarginalCost"], s=60)

for _, row in agg.iterrows():
    plt.text(
        row["CumCapacity"],
        row["MarginalCost"] + 1,
        row["Source"],
        fontsize=9,
        rotation=40,
        ha="right",
    )

plt.xlabel("Cumulative Capacity (MW)")
plt.ylabel("Marginal Cost (€/MWh)")
plt.title("Switzerland Merit-Order Stack (Hydro Split)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()