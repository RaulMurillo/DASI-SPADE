
package examples.pr1;

import jade.core.Agent;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

import jade.core.AID;
import jade.core.behaviours.*;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;
import jade.domain.DFService;
import jade.domain.FIPAException;
import jade.domain.FIPAAgentManagement.DFAgentDescription;
import jade.domain.FIPAAgentManagement.ServiceDescription;

public class pr1Agent extends Agent {
    // Put agent initializations here
	protected void setup() {
        //DateFormat dFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
		Date date = new Date();
        System.out.println("Hallo! pr1-agent "+getAID().getName()+" is ready. Created at "+date+"."); //dFormat.format(date)

        // Get the title of the book to buy as a start-up argument
		Object[] args = getArguments();
		if (args != null && args.length > 0) {
            // Add a OneHotBehaviour that schedules a request to seller agents every XX time
			addBehaviour(new OneShotBehaviour() {

                @Override
                public void action() {
                    System.out.println("Hallo from behaviour!!\n pr1-agent "+getAID().getName()+" is ready. Created at "+date+".");
                }

            }
        );
        }
		else {
			// Make the agent terminate
			System.out.println("No argument specified");
			doDelete();
		}

    }

    // Put agent clean-up operations here
	protected void takeDown() {
		// Printout a dismissal message
		System.out.println("pr1-agent "+getAID().getName()+" terminating.");
	}

}