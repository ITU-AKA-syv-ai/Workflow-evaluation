import { Link } from "react-router-dom";


export default function Overview() {
  return (
    <div>
      <h1>Welcome to the overview</h1>

      <section id="links">
        <ul>
          <li>
            <Link to="/evaluation-details">
              Go to evaluation details
            </Link>
          </li>
        </ul>
      </section>
    </div>
  );
}
