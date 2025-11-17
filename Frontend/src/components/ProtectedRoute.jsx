const OptionalAuthRoute = ({ children }) => {
  // Routes are accessible with or without authentication
  // Login is optional - users can access features without logging in
  return children;
};

export default OptionalAuthRoute;
