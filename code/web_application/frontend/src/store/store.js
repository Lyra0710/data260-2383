import { configureStore } from "@reduxjs/toolkit";
import fixturesReducer from "../features/fixtures/fixturesSlice";

export const store = configureStore({
    reducer: {
        fixtures: fixturesReducer,
    },
});