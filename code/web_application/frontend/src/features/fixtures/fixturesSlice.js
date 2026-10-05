import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../../api/axios";

function getErrorMessage(error) {
    return (
        error.response?.data?.detail ||
        error.message ||
        "Request failed"
    );
}

export const fetchFixtures = createAsyncThunk(
    "fixtures/fetchFixtures",
    async ({ page = 1, page_size = 10 } = {}, thunkAPI) => {
        try {
            const response = await api.get("/fixtures", {
                params: { page, page_size },
            });

            return response.data;
        } catch (error) {
            return thunkAPI.rejectWithValue(getErrorMessage(error));
        }
    }
);

export const createFixture = createAsyncThunk(
    "fixtures/createFixture",
    async (fixtureData, thunkAPI) => {
        try {
            const response = await api.post("/fixtures", fixtureData);
            return response.data;
        } catch (error) {
            return thunkAPI.rejectWithValue(getErrorMessage(error));
        }
    }
);

export const updateFixture = createAsyncThunk(
    "fixtures/updateFixture",
    async ({ id, data }, thunkAPI) => {
        try {
            const response = await api.put(`/fixtures/${id}`, data);
            return response.data;
        } catch (error) {
            return thunkAPI.rejectWithValue(getErrorMessage(error));
        }
    }
);

export const deleteFixture = createAsyncThunk(
    "fixtures/deleteFixture",
    async (id, thunkAPI) => {
        try {
            await api.delete(`/fixtures/${id}`);
            return id;
        } catch (error) {
            return thunkAPI.rejectWithValue(getErrorMessage(error));
        }
    }
);

const fixturesSlice = createSlice({
    name: "fixtures",
    initialState: {
        items: [],
        loading: false,
        error: null,
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchFixtures.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchFixtures.fulfilled, (state, action) => {
                state.loading = false;
                state.items = action.payload;
            })
            .addCase(fetchFixtures.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(createFixture.fulfilled, (state, action) => {
                state.items.push(action.payload);
            })
            .addCase(updateFixture.fulfilled, (state, action) => {
                const index = state.items.findIndex(
                    (fixture) => fixture.id === action.payload.id
                );

                if (index !== -1) {
                    state.items[index] = action.payload;
                }
            })
            .addCase(deleteFixture.fulfilled, (state, action) => {
                state.items = state.items.filter(
                    (fixture) => fixture.id !== action.payload
                );
            });
    },
});

export default fixturesSlice.reducer;