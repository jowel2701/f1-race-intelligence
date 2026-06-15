from cleaning import clean_drivers
from cleaning import clean_sessions
from cleaning import clean_laps
from cleaning import clean_stints
from cleaning import clean_weather
from cleaning import clean_race_control
from cleaning import clean_car_data
from cleaning import clean_location_data

def run_step(name: str, module) -> None:
    print("\n" + "=" * 60)
    print(f"  {name}")
    print("=" * 60)
    module.main()


def main() -> None:
    run_step("DRIVERS", clean_drivers)
    run_step("SESSIONS", clean_sessions)
    run_step("LAPS", clean_laps)
    run_step("STINTS", clean_stints)
    run_step("WEATHER", clean_weather)
    run_step("RACE CONTROL", clean_race_control)
    run_step("CAR DATA", clean_car_data)
    run_step("LOCATION", clean_location_data)

    print("\n" + "=" * 60)
    print("  LIMPIEZA COMPLETA")
    print("=" * 60)


if __name__ == "__main__":
    main()
