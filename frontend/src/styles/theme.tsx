import { createTheme } from "@mui/material/styles";

export const getTheme = (mode: "light" | "dark") =>
  createTheme({
    palette: {
      mode,
    },
    components: {
      MuiOutlinedInput: {
        styleOverrides: {
          root: ({ theme }) => ({
            "& .MuiOutlinedInput-notchedOutline": {
              borderColor:
                theme.palette.mode === "dark"
                  ? theme.palette.grey[500]
                  : theme.palette.grey[700],
            },
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor:
                theme.palette.mode === "dark"
                  ? theme.palette.grey[300]
                  : theme.palette.grey[900],
            },
            "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
              borderColor: theme.palette.primary.main,
              borderWidth: "2px",
            },
          }),
        },
      },
    },
  });
